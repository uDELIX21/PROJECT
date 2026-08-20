"""Journey J5: payment initiated → provider simulation → webhook → verification →
ledger update → receipt → (duplicate replay safe). Plus failed/reversed paths."""
import hashlib
import hmac
import json

from tests.conftest import auth_headers, login

SECRET = "dev-webhook-secret"


def _setup_billed_student(client, ids, surname="Payjourney"):
    """Admit+enroll a fresh student in B1A, create a fee structure and bill it."""
    csrf = login(client, "admin")
    h = auth_headers(csrf)
    r = client.post("/api/v1/students", headers=h, json={
        "surname": surname, "other_names": "Kid", "gender": "F",
        "date_of_birth": "2018-01-01", "admit": True})
    sid = r.json()["id"]
    r = client.post("/api/v1/enrollments", headers=h, json={
        "student_id": sid, "class_stream_id": str(ids["stream_b1a"])})
    assert r.status_code == 201, r.text
    enr_id = r.json()["id"]

    # structure for grade B1 (grade-specific; does not disturb other tests)
    r = client.post("/api/v1/fees/structures", headers=h, json={
        "academic_year_id": str(ids["year_cur"]), "name": "B1 fees (test)",
        "grade_id": str(ids["grades"]["B1"]),
        "items": [{"fee_type": "TUITION", "display_name": "Tuition",
                   "amount_pesewas": 40000, "period": "PER_TERM"}]})
    assert r.status_code == 201, r.text
    r = client.post("/api/v1/fees/billing/apply", headers=h, json={
        "academic_year_id": str(ids["year_cur"]), "term_id": str(ids["term1"])})
    assert r.status_code == 200
    return csrf, h, sid, enr_id


def test_j5_cash_and_momo_full_cycle(client, ids):
    csrf, h, sid, enr_id = _setup_billed_student(client, ids)

    # balance before: 400.00 GHS owing
    bal = client.get("/api/v1/fees/balances", params={"student_id": sid}).json()
    assert bal["balance_pesewas"] == 40000

    # --- 1. MoMo initiate → PENDING with provider reference (simulated prompt)
    r = client.post("/api/v1/payments/initiate", headers=h, json={
        "student_id": sid, "amount_pesewas": 25000, "method": "MTN_MOMO",
        "term_id": str(ids["term1"]), "payer_name": "Payjourney Mother",
        "payer_phone": "0241112222"})
    assert r.status_code == 201, r.text
    pay = r.json()
    assert pay["status"] == "PENDING"
    assert pay["provider_reference"].startswith("SIM-MTN_")
    # pending money must NOT move the balance (BR-F09)
    assert client.get("/api/v1/fees/balances", params={"student_id": sid}) \
        .json()["balance_pesewas"] == 40000

    # --- 2. unsigned webhook: stored but never applied
    body = {"event_id": "evt-001", "type": "PAYMENT.SUCCESS",
            "provider_reference": pay["provider_reference"]}
    r = client.post(f"/api/v1/payments/webhooks/MTN_MOMO_STUB", json=body)
    assert r.json()["applied"] is False and r.json()["reason"] == "INVALID_SIGNATURE"
    assert client.get(f"/api/v1/payments/{pay['id']}").json()["status"] == "PENDING"

    # --- 3. properly signed success webhook → CONFIRMED + ledger + receipt
    signed_headers = {"X-Webhook-Signature":
                      hmac.new(SECRET.encode(), json.dumps(body).encode(),
                               hashlib.sha256).hexdigest(),
                      "Content-Type": "application/json"}
    r = client.post("/api/v1/payments/webhooks/MTN_MOMO_STUB",
                    content=json.dumps(body), headers=signed_headers)
    assert r.json() == {"applied": True, "payment_status": "CONFIRMED"}, r.text

    view = client.get(f"/api/v1/payments/{pay['id']}").json()
    assert view["status"] == "CONFIRMED"
    assert view["receipt_id"] is not None
    assert view["allocations"] and view["allocations"][0]["amount_pesewas"] == 25000

    bal = client.get("/api/v1/fees/balances", params={"student_id": sid}).json()
    assert bal["balance_pesewas"] == 15000
    assert any(e["category"] == "PAYMENT" for e in bal["entries"])

    # --- 4. duplicate webhook replay → no double posting (BR-F10)
    ledger_before = client.get("/api/v1/fees/balances", params={"student_id": sid}) \
        .json()["entries"]
    r = client.post("/api/v1/payments/webhooks/MTN_MOMO_STUB",
                    content=json.dumps(body), headers=signed_headers)
    assert r.json()["applied"] is False and r.json()["reason"] == "DUPLICATE_EVENT"
    ledger_after = client.get("/api/v1/fees/balances", params={"student_id": sid}) \
        .json()["entries"]
    assert len([e for e in ledger_after if e["category"] == "PAYMENT"]) == \
        len([e for e in ledger_before if e["category"] == "PAYMENT"]) == 1
    assert client.get("/api/v1/fees/balances", params={"student_id": sid}) \
        .json()["balance_pesewas"] == 15000

    # --- 5. receipt content + PDF
    receipt = client.get(f"/api/v1/receipts/{view['receipt_id']}").json()
    assert receipt["amount_pesewas"] == 25000
    assert receipt["receipt_no"]
    assert receipt["balance_after_pesewas"] == 15000
    pdf = client.get(f"/api/v1/receipts/{view['receipt_id']}/pdf")
    assert pdf.status_code == 200 and pdf.content[:5] == b"%PDF-"

    # --- 6. failed payment path: webhook FAILED marks payment, no ledger effect
    r = client.post("/api/v1/payments/initiate", headers=h, json={
        "student_id": sid, "amount_pesewas": 10000, "method": "TELECEL_CASH",
        "term_id": str(ids["term1"])})
    pay2 = r.json()
    fail_body = {"event_id": "evt-002", "type": "PAYMENT.FAILED",
                 "provider_reference": pay2["provider_reference"],
                 "reason": "insufficient funds"}
    signed = {"X-Webhook-Signature": hmac.new(SECRET.encode(),
                                              json.dumps(fail_body).encode(),
                                              hashlib.sha256).hexdigest(),
              "Content-Type": "application/json"}
    r = client.post("/api/v1/payments/webhooks/TELECEL_CASH_STUB",
                    content=json.dumps(fail_body), headers=signed)
    assert r.json()["applied"] is True
    assert client.get(f"/api/v1/payments/{pay2['id']}").json()["status"] == "FAILED"
    assert client.get("/api/v1/fees/balances", params={"student_id": sid}) \
        .json()["balance_pesewas"] == 15000  # unchanged

    # --- 7. reversal (provider webhook): ledger counter-entry + receipt voided
    rev_body = {"event_id": "evt-003", "type": "PAYMENT.REVERSED",
                "provider_reference": pay["provider_reference"]}
    signed = {"X-Webhook-Signature": hmac.new(SECRET.encode(),
                                              json.dumps(rev_body).encode(),
                                              hashlib.sha256).hexdigest(),
              "Content-Type": "application/json"}
    r = client.post("/api/v1/payments/webhooks/MTN_MOMO_STUB",
                    content=json.dumps(rev_body), headers=signed)
    assert r.json()["applied"] is True
    assert client.get(f"/api/v1/payments/{pay['id']}").json()["status"] == "REVERSED"
    bal = client.get("/api/v1/fees/balances", params={"student_id": sid}).json()
    assert bal["balance_pesewas"] == 40000  # back to owing
    cats = [e["category"] for e in bal["entries"]]
    assert cats.count("PAYMENT") == 1 and cats.count("REVERSAL") == 1
    # receipt voided, original preserved (BR-F08)
    receipt = client.get(f"/api/v1/receipts/{view['receipt_id']}").json()
    assert receipt["status"] == "VOIDED" and receipt["receipt_no"]


def test_cash_payment_confirms_immediately(client, ids):
    csrf, h, sid, enr_id = _setup_billed_student(client, ids, surname="Cashpay")
    r = client.post("/api/v1/payments/initiate", headers=h, json={
        "student_id": sid, "amount_pesewas": 40000, "method": "CASH",
        "term_id": str(ids["term1"]), "payer_name": "Cashpay Father"})
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "CONFIRMED" and body["receipt_id"]
    assert client.get("/api/v1/fees/balances", params={"student_id": sid}) \
        .json()["balance_pesewas"] == 0


def test_overpayment_becomes_credit(client, ids):
    csrf, h, sid, enr_id = _setup_billed_student(client, ids, surname="Overpay")
    r = client.post("/api/v1/payments/initiate", headers=h, json={
        "student_id": sid, "amount_pesewas": 45000, "method": "CASH",
        "term_id": str(ids["term1"])})
    assert r.json()["status"] == "CONFIRMED"
    bal = client.get("/api/v1/fees/balances", params={"student_id": sid}).json()
    assert bal["balance_pesewas"] == -5000  # credit balance (BR-F05)
