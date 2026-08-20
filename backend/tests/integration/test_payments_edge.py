"""Payment edge suite (spec §44 Payment Tests): successful, failed, duplicate,
delayed, reversed, refunded transactions — plus webhook security edges."""
import hashlib
import hmac
import json
import uuid

from tests.conftest import auth_headers, login

SECRET = "dev-webhook-secret"


def _setup(client, ids, h, amount=40000, surname="Payedge"):
    r = client.post("/api/v1/students", headers=h, json={
        "surname": surname, "other_names": str(uuid.uuid4())[:6], "gender": "F",
        "date_of_birth": "2018-01-01", "admit": True})
    sid = r.json()["id"]
    r = client.post("/api/v1/enrollments", headers=h, json={
        "student_id": sid, "class_stream_id": str(ids["stream_b1a"])})
    enr_id = r.json()["id"]
    r = client.post("/api/v1/fees/charges", headers=h, json={
        "enrollment_id": enr_id, "fee_type": "TUITION", "display_name": "Tuition",
        "amount_pesewas": amount, "term_id": str(ids["term1"])})
    assert r.status_code == 201, r.text
    return sid, enr_id


def _sign(body: str) -> str:
    return hmac.new(SECRET.encode(), body.encode(), hashlib.sha256).hexdigest()


def _webhook(client, provider, payload, sig=None):
    body = json.dumps(payload)
    return client.post(f"/api/v1/payments/webhooks/{provider}", content=body,
                       headers={"Content-Type": "application/json",
                                "X-Webhook-Signature": sig or _sign(body)})


def _initiate_momo(client, h, sid, amount, term_id):
    r = client.post("/api/v1/payments/initiate", headers=h, json={
        "student_id": sid, "amount_pesewas": amount, "method": "MTN_MOMO",
        "term_id": term_id})
    assert r.status_code == 201, r.text
    return r.json()


def test_delayed_webhook_confirms_pending_payment(client, ids):
    """Delayed success webhook (hours later in prod) still confirms exactly once."""
    h = auth_headers(login(client, "admin"))
    sid, _ = _setup(client, ids, h, surname="Delayed")
    pay = _initiate_momo(client, h, sid, 40000, str(ids["term1"]))
    assert pay["status"] == "PENDING"
    # balance unchanged while pending (BR-F09)
    assert client.get(f"/api/v1/fees/balances?student_id={sid}").json()["balance_pesewas"] == 40000
    # webhook arrives "later"
    r = _webhook(client, "MTN_MOMO_STUB", {
        "event_id": f"delay-{pay['id']}", "type": "PAYMENT.SUCCESS",
        "provider_reference": pay["provider_reference"]})
    assert r.json()["applied"] is True
    assert client.get(f"/api/v1/fees/balances?student_id={sid}").json()["balance_pesewas"] == 0


def test_failed_webhook_marks_payment_and_moves_nothing(client, ids):
    h = auth_headers(login(client, "admin"))
    sid, _ = _setup(client, ids, h, amount=30000, surname="Failed")
    pay = _initiate_momo(client, h, sid, 30000, str(ids["term1"]))
    r = _webhook(client, "MTN_MOMO_STUB", {
        "event_id": f"fail-{pay['id']}", "type": "PAYMENT.FAILED",
        "provider_reference": pay["provider_reference"], "reason": "insufficient funds"})
    assert r.json()["applied"] is True
    view = client.get(f"/api/v1/payments/{pay['id']}").json()
    assert view["status"] == "FAILED"
    assert client.get(f"/api/v1/fees/balances?student_id={sid}").json()["balance_pesewas"] == 30000
    # a late success after FAILED is refused (terminal state)
    r = _webhook(client, "MTN_MOMO_STUB", {
        "event_id": f"fail2-{pay['id']}", "type": "PAYMENT.SUCCESS",
        "provider_reference": pay["provider_reference"]})
    assert r.json()["applied"] is False and r.json()["reason"] == "PAYMENT_TERMINAL"
    assert client.get(f"/api/v1/fees/balances?student_id={sid}").json()["balance_pesewas"] == 30000


def test_duplicate_webhooks_are_exactly_once(client, ids):
    h = auth_headers(login(client, "admin"))
    sid, _ = _setup(client, ids, h, amount=50000, surname="Dupweb")
    pay = _initiate_momo(client, h, sid, 50000, str(ids["term1"]))
    payload = {"event_id": f"dup-{pay['id']}", "type": "PAYMENT.SUCCESS",
               "provider_reference": pay["provider_reference"]}
    first = _webhook(client, "MTN_MOMO_STUB", payload).json()
    assert first["applied"] is True
    for _ in range(3):  # provider retries
        r = _webhook(client, "MTN_MOMO_STUB", payload).json()
        assert r["applied"] is False and r["reason"] == "DUPLICATE_EVENT"
    assert client.get(f"/api/v1/fees/balances?student_id={sid}").json()["balance_pesewas"] == 0
    # exactly one receipt, exactly one PAYMENT entry
    rcpts = client.get(f"/api/v1/receipts?student_id={sid}").json()["items"]
    assert len(rcpts) == 1
    entries = client.get(f"/api/v1/fees/balances?student_id={sid}").json()["entries"]
    assert sum(1 for e in entries if e["category"] == "PAYMENT") == 1


def test_reversal_webhook_voids_receipt_and_restores_balance(client, ids):
    h = auth_headers(login(client, "admin"))
    sid, _ = _setup(client, ids, h, amount=25000, surname="Reversed")
    pay = _initiate_momo(client, h, sid, 25000, str(ids["term1"]))
    _webhook(client, "MTN_MOMO_STUB", {"event_id": f"rev1-{pay['id']}",
                                       "type": "PAYMENT.SUCCESS",
                                       "provider_reference": pay["provider_reference"]})
    receipt = client.get(f"/api/v1/receipts?student_id={sid}").json()["items"][0]
    assert receipt["status"] == "ISSUED"
    r = _webhook(client, "MTN_MOMO_STUB", {"event_id": f"rev2-{pay['id']}",
                                           "type": "PAYMENT.REVERSED",
                                           "provider_reference": pay["provider_reference"]})
    assert r.json()["applied"] is True
    assert client.get(f"/api/v1/payments/{pay['id']}").json()["status"] == "REVERSED"
    assert client.get(f"/api/v1/fees/balances?student_id={sid}").json()["balance_pesewas"] == 25000
    receipt = client.get(f"/api/v1/receipts?student_id={sid}").json()["items"][0]
    assert receipt["status"] == "VOIDED"  # original preserved, state flipped (BR-F08)
    # replay of the reversal must not double-restore
    r = _webhook(client, "MTN_MOMO_STUB", {"event_id": f"rev2-{pay['id']}",
                                           "type": "PAYMENT.REVERSED",
                                           "provider_reference": pay["provider_reference"]})
    assert r.json()["applied"] is False
    assert client.get(f"/api/v1/fees/balances?student_id={sid}").json()["balance_pesewas"] == 25000


def test_refund_bounds_and_flow(client, ids):
    h = auth_headers(login(client, "admin"))
    sid, _ = _setup(client, ids, h, amount=20000, surname="Refund")
    r = client.post("/api/v1/payments/initiate", headers=h, json={
        "student_id": sid, "amount_pesewas": 20000, "method": "CASH",
        "term_id": str(ids["term1"])})
    pay_id = r.json()["id"]
    # over-refund refused
    bad = client.post(f"/api/v1/payments/{pay_id}/refund", headers=h, json={
        "amount_pesewas": 30000, "reason": "too much"})
    assert bad.status_code == 409
    ok = client.post(f"/api/v1/payments/{pay_id}/refund", headers=h, json={
        "amount_pesewas": 5000, "reason": "overpaid at counter"})
    assert ok.status_code == 200
    assert client.get(f"/api/v1/payments/{pay_id}").json()["status"] == "REFUNDED"
    # refunding a SETTLED payment re-opens the debt: student owes 5000 again
    assert client.get(f"/api/v1/fees/balances?student_id={sid}").json()["balance_pesewas"] == 5000


def test_overpayment_credit_and_fifo(client, ids):
    h = auth_headers(login(client, "admin"))
    sid, enr = _setup(client, ids, h, amount=30000, surname="Overfifo")
    # second charge due later
    client.post("/api/v1/fees/charges", headers=h, json={
        "enrollment_id": enr, "fee_type": "FEEDING", "display_name": "Feeding",
        "amount_pesewas": 10000, "term_id": str(ids["term1"])})
    # pay 35000: settles tuition (30000), 5000 into feeding → part-settled
    r = client.post("/api/v1/payments/initiate", headers=h, json={
        "student_id": sid, "amount_pesewas": 35000, "method": "CASH",
        "term_id": str(ids["term1"])})
    pay = client.get(f"/api/v1/payments/{r.json()['id']}").json()
    alloc = {a["amount_pesewas"] for a in pay["allocations"]}
    assert 30000 in alloc and 5000 in alloc  # FIFO: tuition first
    charges = client.get("/api/v1/fees/charges", params={"student_id": sid}).json()["items"]
    by_type = {c["fee_type"]: c for c in charges}
    assert by_type["TUITION"]["status"] == "SETTLED"
    assert by_type["FEEDING"]["status"] == "PART_SETTLED"
    assert client.get(f"/api/v1/fees/balances?student_id={sid}").json()["balance_pesewas"] == 5000


def test_cash_confirmation_requires_create_payment_perm(client, ids):
    ta_h = auth_headers(login(client, "teacherA"))
    r = client.post("/api/v1/payments/initiate", headers=ta_h, json={
        "student_id": str(ids["st1"]), "amount_pesewas": 1000, "method": "CASH"})
    assert r.status_code == 403


def test_provider_registry_lists_stubs(client, ids):
    h = auth_headers(login(client, "admin"))
    items = client.get("/api/v1/payments/providers").json()["items"]
    codes = {p["code"] for p in items}
    assert {"MTN_MOMO_STUB", "TELECEL_CASH_STUB", "AT_MONEY_STUB"} <= codes
    assert all(p["kind"] == "STUB" for p in items)  # clearly labelled (Agent Rule 20)
