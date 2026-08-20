"""Ledger invariant tests (design §08): balances are always derived, entries are
immutable, corrections are counter-entries. Randomized operation sequences."""
import random
import uuid

from tests.conftest import auth_headers, login


def _student_with_charges(client, ids, h, n_charges=3, amount=10000):
    r = client.post("/api/v1/students", headers=h, json={
        "surname": "Invariant", "other_names": str(uuid.uuid4())[:6], "gender": "M",
        "date_of_birth": "2017-01-01", "admit": True})
    sid = r.json()["id"]
    r = client.post("/api/v1/enrollments", headers=h, json={
        "student_id": sid, "class_stream_id": str(ids["stream_b1a"])})
    enr = r.json()["id"]
    for i in range(n_charges):
        client.post("/api/v1/fees/charges", headers=h, json={
            "enrollment_id": enr, "fee_type": "TUITION", "display_name": f"Charge {i}",
            "amount_pesewas": amount, "term_id": str(ids["term1"])})
    return sid, enr


def test_balance_identity_under_random_operations(client, ids):
    """Σ DEBIT − Σ CREDIT == reported balance after any interleaving."""
    h = auth_headers(login(client, "admin"))
    sid, enr = _student_with_charges(client, ids, h, n_charges=4, amount=20000)
    rng = random.Random(42)
    expected = 4 * 20000
    payments = []
    for step in range(12):
        op = rng.choice(["pay", "waive", "adjust_credit", "adjust_debit"])
        if op == "pay":
            amount = rng.randint(1000, 15000)
            r = client.post("/api/v1/payments/initiate", headers=h, json={
                "student_id": sid, "amount_pesewas": amount, "method": "CASH",
                "term_id": str(ids["term1"])})
            payments.append(r.json()["id"])
            expected -= amount
        elif op == "waive":
            amount = rng.randint(500, 3000)
            client.post("/api/v1/fees/waivers", headers=h, json={
                "enrollment_id": enr, "kind": "WAIVER", "amount_pesewas": amount,
                "term_id": str(ids["term1"]), "reason": "invariant fuzz"})
            expected -= amount
        elif op == "adjust_credit":
            amount = rng.randint(200, 1500)
            client.post("/api/v1/fees/adjustments", headers=h, json={
                "enrollment_id": enr, "direction": "CREDIT", "amount_pesewas": amount,
                "term_id": str(ids["term1"]), "reason": "invariant fuzz"})
            expected -= amount
        else:
            amount = rng.randint(200, 1500)
            client.post("/api/v1/fees/adjustments", headers=h, json={
                "enrollment_id": enr, "direction": "DEBIT", "amount_pesewas": amount,
                "term_id": str(ids["term1"]), "reason": "invariant fuzz"})
            expected += amount
        bal = client.get(f"/api/v1/fees/balances?student_id={sid}").json()["balance_pesewas"]
        assert bal == expected, f"step {step} ({op}): balance {bal} != expected {expected}"


def test_reversal_preserves_original_entries(client, ids):
    h = auth_headers(login(client, "admin"))
    sid, _ = _student_with_charges(client, ids, h, n_charges=1, amount=15000)
    r = client.post("/api/v1/payments/initiate", headers=h, json={
        "student_id": sid, "amount_pesewas": 15000, "method": "CASH",
        "term_id": str(ids["term1"])})
    pay_id = r.json()["id"]
    entries_before = client.get(f"/api/v1/fees/balances?student_id={sid}").json()["entries"]
    n_before = len(entries_before)
    client.post(f"/api/v1/payments/{pay_id}/reverse", headers=h,
                json={"reason": "recorded against wrong student"})
    entries_after = client.get(f"/api/v1/fees/balances?student_id={sid}").json()["entries"]
    # nothing deleted: original entries remain + one REVERSAL added
    assert len(entries_after) == n_before + 1
    assert any(e["category"] == "REVERSAL" for e in entries_after)
    assert any(e["category"] == "PAYMENT" for e in entries_after)  # original survives
    assert client.get(f"/api/v1/fees/balances?student_id={sid}").json()["balance_pesewas"] == 15000


def test_receipt_immutable_except_void(client, ids):
    h = auth_headers(login(client, "admin"))
    sid, _ = _student_with_charges(client, ids, h, n_charges=1, amount=9000)
    r = client.post("/api/v1/payments/initiate", headers=h, json={
        "student_id": sid, "amount_pesewas": 9000, "method": "CASH",
        "term_id": str(ids["term1"])})
    receipt_id = r.json()["receipt_id"]
    before = client.get(f"/api/v1/receipts/{receipt_id}").json()
    # double-void refused; no delete/edit endpoints exist
    client.post(f"/api/v1/receipts/{receipt_id}/void", headers=h,
                json={"reason": "mistake"})
    again = client.post(f"/api/v1/receipts/{receipt_id}/void", headers=h,
                        json={"reason": "again"})
    assert again.status_code == 409
    after = client.get(f"/api/v1/receipts/{receipt_id}").json()
    assert after["status"] == "VOIDED"
    assert after["receipt_no"] == before["receipt_no"]  # identity preserved
    assert after["amount_pesewas"] == before["amount_pesewas"]
    assert client.delete(f"/api/v1/receipts/{receipt_id}", headers=h).status_code in (404, 405)
    assert client.patch(f"/api/v1/receipts/{receipt_id}", headers=h,
                        json={}).status_code in (404, 405)


def test_charge_statuses_track_settlement(client, ids):
    h = auth_headers(login(client, "admin"))
    sid, enr = _student_with_charges(client, ids, h, n_charges=1, amount=12000)
    charges = client.get("/api/v1/fees/charges", params={"student_id": sid}).json()["items"]
    assert charges[0]["status"] == "ACTIVE"
    client.post("/api/v1/payments/initiate", headers=h, json={
        "student_id": sid, "amount_pesewas": 5000, "method": "CASH",
        "term_id": str(ids["term1"])})
    charges = client.get("/api/v1/fees/charges", params={"student_id": sid}).json()["items"]
    assert charges[0]["status"] == "PART_SETTLED"
    client.post("/api/v1/payments/initiate", headers=h, json={
        "student_id": sid, "amount_pesewas": 7000, "method": "CASH",
        "term_id": str(ids["term1"])})
    charges = client.get("/api/v1/fees/charges", params={"student_id": sid}).json()["items"]
    assert charges[0]["status"] == "SETTLED"


def test_no_student_balance_column_in_schema(client, ids):
    """REQ-FIN-01: balance must be derived — no stored balance field on students."""
    from sqlalchemy import inspect
    from app.core.db import get_engine
    cols = {c["name"] for c in inspect(get_engine()).get_columns("students")}
    assert "balance" not in cols
    assert not any("balance" in c for c in cols)
