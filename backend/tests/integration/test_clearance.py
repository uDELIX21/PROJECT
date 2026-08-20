"""Financial clearance: configurable policies gate report publication (REQ-CLR-01,
BR-F11, BR-R02) with audited overrides."""
from tests.conftest import auth_headers, login


def _jhs_student(client, ids, surname):
    csrf = login(client, "admin")
    h = auth_headers(csrf)
    r = client.post("/api/v1/students", headers=h, json={
        "surname": surname, "other_names": "Clear", "gender": "M",
        "date_of_birth": "2012-05-05", "admit": True})
    sid = r.json()["id"]
    r = client.post("/api/v1/enrollments", headers=h, json={
        "student_id": sid, "class_stream_id": str(ids["stream_jhs3a"])})
    return csrf, h, sid, r.json()["id"]


def _policy(client, h, ids):
    """REPORT_CARD policy: 100% of term charges, scoped to JHS-3 grade only so it
    cannot disturb report publication in other tests."""
    r = client.post("/api/v1/fees/clearance/policies", headers=h, json={
        "academic_year_id": str(ids["year_cur"]), "term_id": str(ids["term1"]),
        "clearance_type": "REPORT_CARD", "mode": "PERCENT_OF_CHARGES",
        "threshold": 10000, "grade_id": str(ids["grades"]["JHS3"])})
    assert r.status_code == 201, r.text


def _bill_jhs(client, h, ids):
    r = client.post("/api/v1/fees/structures", headers=h, json={
        "academic_year_id": str(ids["year_cur"]), "name": "JHS3 fees (clearance test)",
        "grade_id": str(ids["grades"]["JHS3"]),
        "items": [{"fee_type": "TUITION", "display_name": "Tuition",
                   "amount_pesewas": 60000, "period": "PER_TERM"}]})
    assert r.status_code == 201, r.text
    r = client.post("/api/v1/fees/billing/apply", headers=h, json={
        "academic_year_id": str(ids["year_cur"]), "term_id": str(ids["term1"])})
    assert r.status_code == 200


def test_publication_blocked_then_clear_after_payment(client, ids):
    csrf, h, sid, enr_id = _jhs_student(client, ids, surname="Gatekid")
    _policy(client, h, ids)
    _bill_jhs(client, h, ids)

    # evaluate: nothing paid → BLOCKED
    ev = client.post("/api/v1/fees/clearance/evaluate", headers=h, params={
        "student_id": sid, "term_id": str(ids["term1"])})
    assert ev.json()["state"] == "BLOCKED"
    assert ev.json()["charged_pesewas"] == 60000

    # generate report, publication must be gated (BR-R02)
    r = client.post("/api/v1/reports/generate", headers=h, json={
        "student_id": sid, "term_id": str(ids["term1"])})
    assert r.status_code == 201, r.text
    report_id = r.json()["id"]
    r = client.post(f"/api/v1/reports/{report_id}/publish", headers=h, json={})
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "CLEARANCE_BLOCKED"

    # pay in full → CLEAR → publish succeeds
    r = client.post("/api/v1/payments/initiate", headers=h, json={
        "student_id": sid, "amount_pesewas": 60000, "method": "CASH",
        "term_id": str(ids["term1"])})
    assert r.json()["status"] == "CONFIRMED"
    ev = client.post("/api/v1/fees/clearance/evaluate", headers=h, params={
        "student_id": sid, "term_id": str(ids["term1"])})
    assert ev.json()["state"] == "CLEAR"
    r = client.post(f"/api/v1/reports/{report_id}/publish", headers=h, json={})
    assert r.status_code == 200
    assert r.json()["clearance"]["state"] == "CLEAR"


def test_waiver_override_unblocks_and_is_audited(client, ids):
    csrf, h, sid, enr_id = _jhs_student(client, ids, surname="Waivegate")
    _policy(client, h, ids)
    _bill_jhs(client, h, ids)
    r = client.post("/api/v1/reports/generate", headers=h, json={
        "student_id": sid, "term_id": str(ids["term1"])})
    report_id = r.json()["id"]

    # override without reason rejected
    bad = client.post("/api/v1/fees/clearance/override", headers=h, json={
        "student_id": sid, "term_id": str(ids["term1"]),
        "clearance_type": "REPORT_CARD", "state": "WAIVED", "reason": "x"})
    assert bad.status_code == 422  # reason min length 5

    # authorized waiver override (audited)
    r = client.post("/api/v1/fees/clearance/override", headers=h, json={
        "student_id": sid, "term_id": str(ids["term1"]),
        "clearance_type": "REPORT_CARD", "state": "WAIVED",
        "reason": "Headteacher waiver — staff child, board resolution 12/2026"})
    assert r.status_code == 200 and r.json()["state"] == "WAIVED"

    r = client.post(f"/api/v1/reports/{report_id}/publish", headers=h, json={})
    assert r.status_code == 200
    assert r.json()["clearance"]["state"] == "WAIVED"

    audit = client.get("/api/v1/audit", params={
        "action": "clearance.overridden"}).json()["items"]
    hit = next(a for a in audit if "board resolution" in (a["reason"] or ""))
    assert hit["previous"]["state"] == "BLOCKED"
    assert hit["new"]["state"] == "WAIVED"


def test_pending_payment_forces_reconciliation_state(client, ids):
    csrf, h, sid, enr_id = _jhs_student(client, ids, surname="Pendinggate")
    _policy(client, h, ids)
    _bill_jhs(client, h, ids)
    r = client.post("/api/v1/payments/initiate", headers=h, json={
        "student_id": sid, "amount_pesewas": 60000, "method": "MTN_MOMO",
        "term_id": str(ids["term1"])})
    assert r.json()["status"] == "PENDING"
    ev = client.post("/api/v1/fees/clearance/evaluate", headers=h, params={
        "student_id": sid, "term_id": str(ids["term1"])})
    assert ev.json()["state"] == "PENDING_RECONCILIATION"


def test_unbilled_students_stay_clear(client, ids):
    """No charges ⇒ nothing gates (design §08.3)."""
    csrf, h, sid, enr_id = _jhs_student(client, ids, surname="Nobill")
    _policy(client, h, ids)  # policy exists but nothing billed for this student
    ev = client.post("/api/v1/fees/clearance/evaluate", headers=h, params={
        "student_id": sid, "term_id": str(ids["term1"])})
    assert ev.json()["state"] == "CLEAR"


def test_teacher_cannot_evaluate_clearance(client, ids):
    login(client, "teacherA")
    r = client.post("/api/v1/fees/clearance/evaluate", params={
        "student_id": str(ids["st1"]), "term_id": str(ids["term1"])})
    assert r.status_code == 403
