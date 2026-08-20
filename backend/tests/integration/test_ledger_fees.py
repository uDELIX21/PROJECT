"""Ledger & fee engine: billing runs, balances, waivers, adjustments, reversals,
allocation FIFO — and the guarantee that history is never silently deleted."""
from tests.conftest import auth_headers, login


def _setup(client, ids, surname="Ledgerkid", band="B1"):
    csrf = login(client, "admin")
    h = auth_headers(csrf)
    r = client.post("/api/v1/students", headers=h, json={
        "surname": surname, "other_names": "Test", "gender": "M",
        "date_of_birth": "2018-02-02", "admit": True})
    sid = r.json()["id"]
    stream = ids["stream_b1a"] if band == "B1" else ids["stream_b2a"]
    r = client.post("/api/v1/enrollments", headers=h, json={
        "student_id": sid, "class_stream_id": str(stream)})
    enr_id = r.json()["id"]
    grade_code = "B1" if band == "B1" else "B2"
    r = client.post("/api/v1/fees/structures", headers=h, json={
        "academic_year_id": str(ids["year_cur"]), "name": f"{band} fees (ledger test)",
        "grade_id": str(ids["grades"][grade_code]),
        "items": [
            {"fee_type": "TUITION", "display_name": "Tuition",
             "amount_pesewas": 50000, "period": "PER_TERM"},
            {"fee_type": "ICT_LAB", "display_name": "ICT Lab",
             "amount_pesewas": 8000, "period": "PER_TERM"}]})
    assert r.status_code == 201, r.text
    return csrf, h, sid, enr_id


def test_billing_preview_apply_idempotent(client, ids):
    csrf, h, sid, enr_id = _setup(client, ids, surname="Billme")
    pv = client.post("/api/v1/fees/billing/preview", headers=h, json={
        "academic_year_id": str(ids["year_cur"]), "term_id": str(ids["term1"])})
    mine = next(x for x in pv.json()["items"] if x["student_id"] == sid)
    assert {c["fee_type"] for c in mine["charges"]} == {"TUITION", "ICT_LAB"}

    r1 = client.post("/api/v1/fees/billing/apply", headers=h, json={
        "academic_year_id": str(ids["year_cur"]), "term_id": str(ids["term1"])})
    created_first = r1.json()["created"]
    assert created_first >= 2

    bal = client.get("/api/v1/fees/balances", params={"student_id": sid}).json()
    assert bal["balance_pesewas"] == 58000

    # second run: nothing new (idempotent — no double billing)
    r2 = client.post("/api/v1/fees/billing/apply", headers=h, json={
        "academic_year_id": str(ids["year_cur"]), "term_id": str(ids["term1"])})
    assert r2.json()["created"] == 0
    assert client.get("/api/v1/fees/balances", params={"student_id": sid}) \
        .json()["balance_pesewas"] == 58000


def test_waiver_and_adjustment_flow(client, ids):
    csrf, h, sid, enr_id = _setup(client, ids, surname="Waivekid")
    client.post("/api/v1/fees/billing/apply", headers=h, json={
        "academic_year_id": str(ids["year_cur"]), "term_id": str(ids["term1"])})

    # scholarship waiver of 25% (reason required)
    r = client.post("/api/v1/fees/waivers", headers=h, json={
        "enrollment_id": enr_id, "kind": "SCHOLARSHIP", "pct": 25.0,
        "term_id": str(ids["term1"]),
        "reason": "Mission scholarship — approved by board."})
    assert r.status_code == 201, r.text
    waived = r.json()["amount_pesewas"]
    assert waived == 14500  # 25% of 580.00

    bal = client.get("/api/v1/fees/balances", params={"student_id": sid}).json()
    assert bal["balance_pesewas"] == 58000 - waived

    # waiver without reason rejected
    bad = client.post("/api/v1/fees/waivers", headers=h, json={
        "enrollment_id": enr_id, "kind": "WAIVER", "amount_pesewas": 100,
        "term_id": str(ids["term1"]), "reason": "no"})
    assert bad.status_code == 422  # reason min_length 5

    # credit adjustment (audited)
    r = client.post("/api/v1/fees/adjustments", headers=h, json={
        "enrollment_id": enr_id, "direction": "CREDIT", "amount_pesewas": 3500,
        "term_id": str(ids["term1"]), "reason": "Fee error correction (duplicate levy)"})
    assert r.status_code == 201
    bal = client.get("/api/v1/fees/balances", params={"student_id": sid}).json()
    assert bal["balance_pesewas"] == 58000 - waived - 3500
    audit = client.get("/api/v1/audit", params={"action": "adjustment.added"}).json()["items"]
    assert audit and audit[0]["reason"].startswith("Fee error")


def test_manual_reversal_keeps_history(client, ids):
    """BR-F02/F08: corrections are counter-entries; originals survive."""
    csrf, h, sid, enr_id = _setup(client, ids, surname="Reversekid")
    r = client.post("/api/v1/payments/initiate", headers=h, json={
        "student_id": sid, "amount_pesewas": 20000, "method": "CASH",
        "term_id": str(ids["term1"])})
    pay_id = r.json()["id"]
    bal = client.get("/api/v1/fees/balances", params={"student_id": sid}).json()
    assert bal["balance_pesewas"] == -20000

    # bursar-level reversal (VOID_PAYMENT)
    r = client.post(f"/api/v1/payments/{pay_id}/reverse", headers=h,
                    json={"reason": "Recorded against wrong student by mistake"})
    assert r.status_code == 200
    bal = client.get("/api/v1/fees/balances", params={"student_id": sid}).json()
    assert bal["balance_pesewas"] == 0
    cats = [e["category"] for e in bal["entries"]]
    assert "PAYMENT" in cats and "REVERSAL" in cats  # both rows exist — nothing deleted
    audit = client.get("/api/v1/audit", params={
        "action": "payment.reversed", "entity_id": pay_id}).json()["items"]
    assert audit and "wrong student" in audit[0]["reason"]


def test_fifo_allocation_and_charge_status(client, ids):
    csrf, h, sid, enr_id = _setup(client, ids, surname="Fifokid")
    client.post("/api/v1/fees/billing/apply", headers=h, json={
        "academic_year_id": str(ids["year_cur"]), "term_id": str(ids["term1"])})
    # pay exactly the tuition amount → tuition SETTLED, ICT still ACTIVE
    r = client.post("/api/v1/payments/initiate", headers=h, json={
        "student_id": sid, "amount_pesewas": 50000, "method": "CASH",
        "term_id": str(ids["term1"])})
    view = client.get(f"/api/v1/payments/{r.json()['id']}").json()
    charges = client.get("/api/v1/fees/charges", params={"student_id": sid}).json()["items"]
    by_type = {c["fee_type"]: c for c in charges}
    assert by_type["TUITION"]["status"] == "SETTLED"
    assert by_type["ICT_LAB"]["status"] == "ACTIVE"
    assert view["allocations"][0]["amount_pesewas"] == 50000


def test_refund_flow(client, ids):
    csrf, h, sid, enr_id = _setup(client, ids, surname="Refundkid")
    r = client.post("/api/v1/payments/initiate", headers=h, json={
        "student_id": sid, "amount_pesewas": 30000, "method": "CASH",
        "term_id": str(ids["term1"])})
    pay_id = r.json()["id"]
    r = client.post(f"/api/v1/payments/{pay_id}/refund", headers=h, json={
        "amount_pesewas": 10000, "reason": "Overpaid at counter; refunding difference"})
    assert r.status_code == 200
    assert client.get(f"/api/v1/payments/{pay_id}").json()["status"] == "REFUNDED"
    # balance: -30000 paid, then refund credit of 10000 → -20000
    assert client.get("/api/v1/fees/balances", params={"student_id": sid}) \
        .json()["balance_pesewas"] == -20000


def test_role_guards_on_finance(client, ids):
    login(client, "teacherA")
    assert client.get("/api/v1/fees/charges").status_code == 403
    assert client.get("/api/v1/fees/balances",
                      params={"student_id": str(ids["st1"])}).status_code == 403
    login(client, "bursar")
    assert client.get("/api/v1/fees/charges").status_code == 200
    # bursar cannot reverse (VOID_PAYMENT reserved)
    login(client, "bursar")
    csrf_b = auth_headers(login(client, "bursar"))
    # create a cash payment as bursar then try to reverse without VOID_PAYMENT
    r = client.post("/api/v1/payments/initiate", headers=csrf_b, json={
        "student_id": str(ids["st1"]), "amount_pesewas": 1000, "method": "CASH"})
    if r.status_code == 201:  # st1 may have no charges; payment still records
        rev = client.post(f"/api/v1/payments/{r.json()['id']}/reverse", headers=csrf_b,
                          json={"reason": "bursar should not void"})
        assert rev.status_code == 403


def test_parent_balance_scope(client, ids):
    login(client, "parentU")
    ok = client.get("/api/v1/fees/balances", params={"student_id": str(ids["st1"])})
    assert ok.status_code == 200
    hidden = client.get("/api/v1/fees/balances", params={"student_id": str(ids["st3"])})
    assert hidden.status_code == 404  # uniform: not another family's finances
