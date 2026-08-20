"""Security sweep (spec §44 Security Tests): every representative endpoint ×
every role. Authorization gates are probed with bodies that fail BUSINESS
validation after the gate — so 422/409/404 prove the gate passed, while
401/403 prove it held. Scoping rules verified separately below."""
import pytest

from app import rbac
from tests.conftest import auth_headers, login

# endpoint probes: (method, path-factory, json body or None, required permission)
# Bodies are deliberately invalid-but-parseable so an authorized request fails
# with business/validation errors (>=400 but NOT 401/403).
PROBES = [
    ("GET", "/students", None, rbac.VIEW_STUDENT),
    ("POST", "/students", {"surname": "", "other_names": "x", "gender": "F",
                           "date_of_birth": "2020-01-01"}, rbac.EDIT_STUDENT),
    ("GET", "/parents", None, rbac.VIEW_PARENT),
    ("GET", "/teachers", None, rbac.VIEW_TEACHER),
    ("POST", "/enrollments", {"student_id": "00000000-0000-0000-0000-000000000000",
                              "class_stream_id": "00000000-0000-0000-0000-000000000000"},
     rbac.MANAGE_ENROLLMENT),
    ("PUT", "/assessments/schemes", {"academic_year_id": "00000000-0000-0000-0000-000000000000",
                                     "term_id": "00000000-0000-0000-0000-000000000000",
                                     "grade_id": "00000000-0000-0000-0000-000000000000",
                                     "components": []}, rbac.MANAGE_GRADES_CONFIG),
    ("GET", "/attendance/compliance?term_id=00000000-0000-0000-0000-000000000000", None,
     rbac.MANAGE_ATTENDANCE),
    ("POST", "/reports/generate", {"student_id": "00000000-0000-0000-0000-000000000000",
                                   "term_id": "00000000-0000-0000-0000-000000000000"},
     rbac.MANAGE_REPORTS),
    ("GET", "/fees/charges", None, rbac.VIEW_FINANCE),
    ("POST", "/fees/billing/apply", {"academic_year_id": "00000000-0000-0000-0000-000000000000",
                                     "term_id": "00000000-0000-0000-0000-000000000000"},
     rbac.MANAGE_FEES),
    ("POST", "/payments/initiate", {"student_id": "00000000-0000-0000-0000-000000000000",
                                    "amount_pesewas": 100, "method": "CASH"},
     rbac.CREATE_PAYMENT),
    ("POST", "/payments/00000000-0000-0000-0000-000000000000/reverse",
     {"reason": "security sweep probe"}, rbac.VOID_PAYMENT),
    ("POST", "/fees/waivers", {"enrollment_id": "00000000-0000-0000-0000-000000000000",
                               "kind": "WAIVER", "amount_pesewas": 100,
                               "reason": "security sweep probe"}, rbac.GRANT_WAIVER),
    ("POST", "/fees/clearance/override",
     {"student_id": "00000000-0000-0000-0000-000000000000",
      "term_id": "00000000-0000-0000-0000-000000000000", "state": "WAIVED",
      "reason": "security sweep probe"}, rbac.MANAGE_CLEARANCE),
    ("GET", "/communications/sms-log", None, rbac.SEND_COMMUNICATION),
    ("POST", "/appraisals", {"teacher_id": "00000000-0000-0000-0000-000000000000",
                             "period_from": "2026-09-07", "period_to": "2026-12-10"},
     rbac.APPRAISE_TEACHER),
    ("POST", "/discipline", {"student_id": "00000000-0000-0000-0000-000000000000",
                             "category": "OTHER", "description": "security sweep probe"},
     rbac.MANAGE_DISCIPLINE),
    ("POST", "/imports/upload", None, rbac.IMPORT_DATA),  # missing file → 422 if authorized
    ("GET", "/users", None, rbac.MANAGE_USERS),
    ("GET", "/audit", None, rbac.VIEW_AUDIT),
]

ROLES = {
    "admin": rbac.SUPER_ADMIN,
    "head": rbac.HEAD_TEACHER,
    "bursar": rbac.BURSAR,
    "teacherA": rbac.TEACHER,
    "parentU": rbac.PARENT,
}

DENIED = (401, 403)


@pytest.mark.parametrize("username,role_code", list(ROLES.items()))
def test_permission_gates(client, ids, username, role_code):
    h = auth_headers(login(client, username))
    have = rbac.ROLE_MATRIX[role_code]
    for method, path, body, perm in PROBES:
        if method == "GET":
            r = client.get(f"/api/v1{path}", headers=h)
        else:
            r = client.request(method, f"/api/v1{path}", headers=h, json=body)
        if perm in have:
            # gate passed: any business/validation error is fine, auth errors are not
            assert r.status_code not in DENIED, \
                f"{username} should pass the gate for {method} {path} ({perm})"
        else:
            assert r.status_code in DENIED, \
                f"{username} must be denied for {method} {path} ({perm}); got {r.status_code}"


def test_parent_scoping_matrix(client, ids):
    """Parents reach only their own children's data — uniform 404 elsewhere."""
    h = auth_headers(login(client, "parentU"))
    # own children reachable
    assert client.get(f"/api/v1/students/{ids['st1']}", headers=h).status_code == 200
    assert client.get(f"/api/v1/fees/balances?student_id={ids['st1']}",
                      headers=h).status_code == 200
    assert client.get(f"/api/v1/students/{ids['st1']}/enrollments", headers=h).status_code == 200
    assert client.get(f"/api/v1/students/{ids['st1']}/guardians", headers=h).status_code == 200
    # another family's child: uniform 404 on every surface
    assert client.get(f"/api/v1/students/{ids['st3']}", headers=h).status_code == 404
    assert client.get(f"/api/v1/fees/balances?student_id={ids['st3']}",
                      headers=h).status_code == 404
    assert client.get(f"/api/v1/students/{ids['st3']}/enrollments", headers=h).status_code == 404
    assert client.get(f"/api/v1/students/{ids['st3']}/guardians", headers=h).status_code == 404
    assert client.get(f"/api/v1/pickup?student_id={ids['st3']}", headers=h).status_code == 404
    # writes always denied for parents
    assert client.post("/api/v1/students", headers=h, json={
        "surname": "X", "other_names": "Y", "gender": "F",
        "date_of_birth": "2020-01-01"}).status_code == 403


def test_teacher_scoping_matrix(client, ids):
    """Teachers reach only assigned classes/subjects (REQ-MRK-01/TCH-02)."""
    admin_h = auth_headers(login(client, "admin"))
    # student fully outside teacherA's scope: enrolled in JHS3A (no assignment)
    r = client.post("/api/v1/students", headers=admin_h, json={
        "surname": "Sweepkid", "other_names": "Jhs", "gender": "M",
        "date_of_birth": "2012-01-01", "admit": True})
    jhs_sid = r.json()["id"]
    client.post("/api/v1/enrollments", headers=admin_h, json={
        "student_id": jhs_sid, "class_stream_id": str(ids["stream_jhs3a"])})

    h = auth_headers(login(client, "teacherA"))
    # assigned class roster reachable
    assert client.get(f"/api/v1/classes/streams/{ids['stream_b1a']}/roster",
                      headers=h).status_code == 200
    # unassigned class: uniform 404
    assert client.get(f"/api/v1/classes/streams/{ids['stream_jhs3a']}/roster",
                      headers=h).status_code == 404
    # students outside assignment scope: uniform 404
    assert client.get(f"/api/v1/students/{jhs_sid}", headers=h).status_code == 404
    # finance is gated by permission for teachers (403) — never visible
    assert client.get(f"/api/v1/fees/balances?student_id={jhs_sid}",
                      headers=h).status_code in (403, 404)
    # sync mutations into an unassigned sheet: REJECTED verdict
    import uuid as _uuid
    r = client.post("/api/v1/sync/mutations", headers=h, json={"mutations": [{
        "client_mutation_id": str(_uuid.uuid4()), "entity_type": "ASSESSMENT_SCORE",
        "payload": {"assessment_id": "00000000-0000-0000-0000-000000000000",
                    "enrollment_id": "00000000-0000-0000-0000-000000000000",
                    "raw_score": 50}}]})
    assert r.status_code == 200  # batch envelope; per-mutation rejection inside


def test_unauthenticated_access_denied_everywhere(client, ids):
    """No session → 401 on every protected surface."""
    for method, path, body, _perm in PROBES:
        if method == "GET":
            r = client.get(f"/api/v1{path}")
        else:
            r = client.request(method, f"/api/v1{path}", json=body)
        assert r.status_code == 401, f"unauthenticated {method} {path} → {r.status_code}"


def test_webhook_endpoint_rejects_bad_signature_no_session_needed(client, ids):
    """Webhooks authenticate by signature only; garbage signature applies nothing."""
    r = client.post("/api/v1/payments/webhooks/MTN_MOMO_STUB",
                    content='{"event_id": "sweep-1", "type": "PAYMENT.SUCCESS"}',
                    headers={"Content-Type": "application/json",
                             "X-Webhook-Signature": "invalid"})
    assert r.status_code == 200 and r.json()["applied"] is False
    assert r.json()["reason"] == "INVALID_SIGNATURE"


def test_unknown_provider_webhook_is_404(client, ids):
    r = client.post("/api/v1/payments/webhooks/NO_SUCH_PROVIDER",
                    content="{}", headers={"Content-Type": "application/json"})
    assert r.status_code == 404


def test_audit_not_writable_via_api(client, ids):
    """Audit log is read-only — no write/delete routes exist."""
    h = auth_headers(login(client, "admin"))
    assert client.post("/api/v1/audit", headers=h, json={}).status_code in (404, 405)
    assert client.delete("/api/v1/audit", headers=h).status_code in (404, 405)
    assert client.patch("/api/v1/audit", headers=h, json={}).status_code in (404, 405)


def test_error_envelope_never_leaks_stack_traces(client, ids):
    h = auth_headers(login(client, "admin"))
    r = client.get("/api/v1/students/00000000-0000-0000-0000-000000000000", headers=h)
    body = r.text
    assert r.status_code == 404
    assert "Traceback" not in body and "sqlalchemy" not in body.lower()
    assert r.json()["error"]["code"] == "NOT_FOUND"
