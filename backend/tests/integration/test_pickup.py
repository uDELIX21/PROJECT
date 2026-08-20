"""Authorized pickup: per-student, expiry-aware, audited, parent-scoped (REQ-PKU-01)."""
from tests.conftest import auth_headers, login


def test_pickup_lifecycle(client, ids):
    admin_h = auth_headers(login(client, "admin"))

    r = client.post("/api/v1/pickup", headers=admin_h, json={
        "student_id": str(ids["st1"]), "person_name": "Adwoa Niece",
        "relationship": "AUNT", "phone": "0209998888",
        "id_reference": "GHA-ID-12345", "expires_on": "2027-08-01"})
    assert r.status_code == 201, r.text
    auth_id = r.json()["id"]

    listing = client.get("/api/v1/pickup", headers=admin_h,
                         params={"student_id": str(ids["st1"])}).json()["items"]
    mine = next(a for a in listing if a["id"] == auth_id)
    assert mine["status"] == "ACTIVE" and mine["phone"] == "+233209998888"
    assert mine["created_by"]  # creator recorded (BR-P03)

    # expiry must be in the future
    bad = client.post("/api/v1/pickup", headers=admin_h, json={
        "student_id": str(ids["st1"]), "person_name": "Late Expiry",
        "expires_on": "2020-01-01"})
    assert bad.status_code == 409 and bad.json()["error"]["code"] == "EXPIRY_INVALID"

    # revoke with reason (audited)
    r = client.post(f"/api/v1/pickup/{auth_id}/revoke", headers=admin_h,
                    json={"reason": "Family changed pickup arrangements"})
    assert r.status_code == 200 and r.json()["status"] == "REVOKED"
    audit = client.get("/api/v1/audit", headers=admin_h,
                       params={"action": "pickup.revoked"}).json()["items"]
    assert any("pickup arrangements" in (a["reason"] or "") for a in audit)

    # parent scope: parentU sees st1 list, not st3's
    parent_h = auth_headers(login(client, "parentU"))
    assert client.get("/api/v1/pickup", headers=parent_h,
                      params={"student_id": str(ids["st1"])}).status_code == 200
    assert client.get("/api/v1/pickup", headers=parent_h,
                      params={"student_id": str(ids["st3"])}).status_code == 404
    # parents cannot create authorizations
    assert client.post("/api/v1/pickup", headers=parent_h, json={
        "student_id": str(ids["st1"]), "person_name": "Self Added"}).status_code == 403


def test_expired_authorization_reports_expired(client, ids):
    """BR-P03: expiry passes automatically without anyone touching the row."""
    admin_h = auth_headers(login(client, "admin"))
    r = client.post("/api/v1/pickup", headers=admin_h, json={
        "student_id": str(ids["st2"]), "person_name": "Temp Driver",
        "phone": "0207776666", "expires_on": "2027-01-01"})
    auth_id = r.json()["id"]
    # force-expire by rewriting the date directly (simulates time passing)
    import uuid as _uuid

    from app.core.db import get_session_factory
    from app.models.operations import PickupAuthorization
    from datetime import date
    db = get_session_factory()()
    row = db.get(PickupAuthorization, _uuid.UUID(auth_id))
    row.expires_on = date(2026, 1, 1)
    db.commit()
    db.close()
    listing = client.get("/api/v1/pickup", headers=admin_h,
                         params={"student_id": str(ids["st2"])}).json()["items"]
    mine = next(a for a in listing if a["id"] == auth_id)
    assert mine["status"] == "EXPIRED"


def test_early_childhood_overview(client, ids):
    admin_h = auth_headers(login(client, "admin"))
    # give the KG stream an enrollment + authorization
    r = client.post("/api/v1/students", headers=admin_h, json={
        "surname": "Pickupkid", "other_names": "Ecd", "gender": "F",
        "date_of_birth": "2022-04-04", "admit": True})
    sid = r.json()["id"]
    client.post("/api/v1/enrollments", headers=admin_h, json={
        "student_id": sid, "class_stream_id": str(ids["stream_kg1a"])})
    client.post("/api/v1/pickup", headers=admin_h, json={
        "student_id": sid, "person_name": "Grandpa Ecd", "relationship": "GRANDPARENT",
        "phone": "0205554444"})
    r = client.get("/api/v1/pickup/early-childhood", headers=admin_h)
    assert r.status_code == 200
    kids = r.json()["items"]
    target = next(k for k in kids if k["student_id"] == sid)
    assert target["authorizations"][0]["person_name"] == "Grandpa Ecd"
