"""Communications: provider abstraction, normalization, opt-out, templates,
event hooks (payment confirmed / report available), notifications (REQ-COM-*)."""
from tests.conftest import auth_headers, login


def test_templates_seeded_and_editable(client, ids):
    h = auth_headers(login(client, "admin"))
    items = client.get("/api/v1/communications/templates").json()["items"]
    codes = {t["event_code"] for t in items}
    assert {"PAYMENT_CONFIRMED", "FEE_REMINDER", "REPORT_AVAILABLE",
            "EMERGENCY_BROADCAST", "ANNOUNCEMENT"} <= codes
    tpl = next(t for t in items if t["event_code"] == "ANNOUNCEMENT")
    r = client.put(f"/api/v1/communications/templates/{tpl['id']}", headers=h, json={
        "template": "{{school_name}} notice: {{message}} (please reply to office)"})
    assert r.status_code == 200
    assert "please reply to office" in r.json()["template"]


def test_broadcast_with_normalization_and_notifications(client, ids):
    h = auth_headers(login(client, "admin"))
    r = client.post("/api/v1/communications/broadcast", headers=h, json={
        "event_code": "ANNOUNCEMENT", "audience": "school",
        "message": "PTA meeting on Friday at 3pm."})
    assert r.status_code == 200, r.text
    assert r.json()["sent"] >= 1

    log = client.get("/api/v1/communications/sms-log", headers=h,
                     params={"limit": 100}).json()["items"]
    ann = [m for m in log if m["event_code"] == "ANNOUNCEMENT"]
    assert ann, "expected broadcast messages in the log"
    assert all(m["recipient_phone"].startswith("+233") for m in ann)  # normalized
    assert all(m["provider_code"] == "CONSOLE" for m in ann)  # stub adapter labelled
    assert all(m["status"] == "SENT" for m in ann)
    assert any("PTA meeting" in m["body_preview"] for m in ann)

    # parentU got an in-app notification for each linked child
    parent_h = auth_headers(login(client, "parentU"))
    notifs = client.get("/api/v1/communications/notifications", headers=parent_h).json()["items"]
    ann_notifs = [n for n in notifs if n["kind"] == "ANNOUNCEMENT"]
    assert len(ann_notifs) >= 2  # st1 + st2


def test_class_audience_and_debtors(client, ids):
    h = auth_headers(login(client, "admin"))
    # B1A: parentU is linked to st1 + st2 there → one guardian recipient, two notices
    r = client.post("/api/v1/communications/broadcast", headers=h, json={
        "event_code": "ANNOUNCEMENT", "audience": "class",
        "class_stream_id": str(ids["stream_b1a"]),
        "message": "Class photo day tomorrow."})
    assert r.status_code == 200 and r.json()["recipients"] >= 1, r.text
    assert r.json()["sent"] >= 1
    # debtors audience with no finance data in test DB → zero recipients, no crash
    r = client.post("/api/v1/communications/broadcast", headers=h, json={
        "event_code": "FEE_REMINDER", "audience": "debtors"})
    assert r.status_code == 200 and r.json()["recipients"] == 0


def test_opt_out_respected(client, ids):
    """BR-N02: opted-out guardians skip bulk SMS (transactional still allowed)."""
    admin_h = auth_headers(login(client, "admin"))
    # dedicated guardian + child in B2A, then opt out directly (no public API for it)
    r = client.post("/api/v1/students", headers=admin_h, json={
        "surname": "Optout", "other_names": "Child", "gender": "F",
        "date_of_birth": "2019-02-02", "admit": True})
    sid = r.json()["id"]
    client.post("/api/v1/enrollments", headers=admin_h, json={
        "student_id": sid, "class_stream_id": str(ids["stream_b2a"])})
    r = client.post("/api/v1/parents", headers=admin_h, json={
        "name": "Optout Guardian", "phone": "0203332222"})
    gid = r.json()["id"]
    client.post(f"/api/v1/parents/{gid}/links", headers=admin_h, json={
        "student_id": sid, "relationship_type": "MOTHER"})

    from app.core.db import get_session_factory
    from app.models.core import ParentGuardian
    import uuid as _uuid
    db = get_session_factory()()
    g = db.get(ParentGuardian, _uuid.UUID(gid))
    g.sms_opt_out = True
    db.commit()
    db.close()

    r = client.post("/api/v1/communications/broadcast", headers=admin_h, json={
        "event_code": "ANNOUNCEMENT", "audience": "class",
        "class_stream_id": str(ids["stream_b2a"]), "message": "opt-out check"})
    assert r.status_code == 200
    assert r.json()["skipped"] >= 1
    log = client.get("/api/v1/communications/sms-log", headers=admin_h,
                     params={"limit": 100}).json()["items"]
    skipped = [m for m in log if m["recipient_phone"] == "+233203332222"]
    assert skipped and all(m["status"] == "SKIPPED" for m in skipped)


def test_payment_and_report_hooks(client, ids):
    """REQ-COM-01 events: payment confirmation + report availability."""
    admin_h = auth_headers(login(client, "admin"))

    # payment for st1 (parentU's child) → PAYMENT_CONFIRMED sms + notification
    r = client.post("/api/v1/payments/initiate", headers=admin_h, json={
        "student_id": str(ids["st1"]), "amount_pesewas": 5000, "method": "CASH"})
    assert r.status_code == 201 and r.json()["status"] == "CONFIRMED"
    log = client.get("/api/v1/communications/sms-log", headers=admin_h,
                     params={"limit": 20}).json()["items"]
    assert any(m["event_code"] == "PAYMENT_CONFIRMED" for m in log)

    parent_h = auth_headers(login(client, "parentU"))
    notifs = client.get("/api/v1/communications/notifications", headers=parent_h).json()["items"]
    assert any(n["kind"] == "PAYMENT_CONFIRMED" for n in notifs)

    # publish st2's report → REPORT_AVAILABLE notification (re-login: cookie was swapped)
    admin_h = auth_headers(login(client, "admin"))
    r = client.post("/api/v1/reports/generate", headers=admin_h, json={
        "student_id": str(ids["st2"]), "term_id": str(ids["term1"])})
    report_id = r.json()["id"]
    client.post(f"/api/v1/reports/{report_id}/finalize", headers=admin_h)
    r = client.post(f"/api/v1/reports/{report_id}/publish", headers=admin_h, json={})
    assert r.status_code == 200
    parent_h = auth_headers(login(client, "parentU"))  # re-login: cookie was swapped
    notifs = client.get("/api/v1/communications/notifications", headers=parent_h).json()["items"]
    assert any(n["kind"] == "REPORT_AVAILABLE" for n in notifs)


def test_notifications_mark_read(client, ids):
    admin_h = auth_headers(login(client, "admin"))
    client.post("/api/v1/communications/broadcast", headers=admin_h, json={
        "event_code": "ANNOUNCEMENT", "audience": "school", "message": "read test"})
    parent_h = auth_headers(login(client, "parentU"))
    notifs = client.get("/api/v1/communications/notifications", headers=parent_h).json()["items"]
    unread = [n["id"] for n in notifs if not n["read"]]
    assert unread
    r = client.post("/api/v1/communications/notifications/read", headers=parent_h,
                    json=unread[:1])
    assert r.status_code == 200 and r.json()["marked"] == 1
    after = client.get("/api/v1/communications/notifications", headers=parent_h,
                       params={"unread_only": "true"}).json()["items"]
    assert all(n["id"] != unread[0] for n in after)


def test_invalid_number_skipped_not_fatal():
    """BR-N01: a bad number is skipped and logged, never crashes the batch."""
    from app.core.db import get_session_factory
    from app.core.ids import uuid7
    from app.services import comms
    db = get_session_factory()()
    from app.models.core import School
    school = db.query(School).first()
    msg = comms.send_sms(db, school_id=school.id, phone="not-a-phone",
                         body="should skip", event_code="ANNOUNCEMENT")
    assert msg.status == "SKIPPED" and msg.error == "invalid_ghana_number"
    db.rollback()
    db.close()
