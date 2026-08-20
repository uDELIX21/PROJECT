"""Discipline module: restricted sensitive records, scoping, parent notification."""
from tests.conftest import auth_headers, login


def test_incident_lifecycle_and_scoping(client, ids):
    admin_h = auth_headers(login(client, "admin"))

    # teacherA (assigned B1A) can log for st1 but not st3 (B2A is ENG-only for A)
    ta_h = auth_headers(login(client, "teacherA"))
    ok = client.post("/api/v1/discipline", headers=ta_h, json={
        "student_id": str(ids["st1"]), "category": "DISRUPTION",
        "description": "Repeatedly interrupted the lesson after warnings.",
        "severity": "MINOR"})
    assert ok.status_code == 201, ok.text
    incident_id = ok.json()["id"]
    # teacherB (owns only B2A) cannot log for st1 in B1A — uniform scope denial
    tb_h = auth_headers(login(client, "teacherB"))
    denied = client.post("/api/v1/discipline", headers=tb_h, json={
        "student_id": str(ids["st1"]), "category": "TRUANCY",
        "description": "Not in class."})
    assert denied.status_code == 404

    # teacherB cannot even list st1's incidents (not their student) — uniform 404
    r = client.get("/api/v1/discipline", headers=tb_h,
                   params={"student_id": str(ids["st1"])})
    assert r.status_code == 404

    # resolve requires a resolution note (re-login admin: cookie was swapped)
    admin_h = auth_headers(login(client, "admin"))
    bad = client.patch(f"/api/v1/discipline/{incident_id}", headers=admin_h,
                       json={"status": "RESOLVED", "resolution": None})
    assert bad.status_code == 409 and bad.json()["error"]["code"] == "RESOLUTION_REQUIRED"
    ok = client.patch(f"/api/v1/discipline/{incident_id}", headers=admin_h,
                      json={"status": "RESOLVED",
                            "resolution": "Parent meeting held; behaviour plan agreed."})
    assert ok.status_code == 200

    # parent sees resolved summaries only — no descriptions leak
    parent_h = auth_headers(login(client, "parentU"))
    r = client.get("/api/v1/discipline", headers=parent_h,
                   params={"student_id": str(ids["st1"])})
    items = r.json()["items"]
    assert len(items) == 1 and items[0]["status"] == "RESOLVED"
    assert "description" not in items[0]
    # and never another family's child
    assert client.get("/api/v1/discipline", headers=parent_h,
                      params={"student_id": str(ids["st3"])}).status_code == 404


def test_parent_notification(client, ids):
    admin_h = auth_headers(login(client, "admin"))
    r = client.post("/api/v1/discipline", headers=admin_h, json={
        "student_id": str(ids["st2"]), "category": "UNIFORM_VIOLATION",
        "description": "Came without the school hat three times this week.",
        "severity": "MINOR"})
    incident_id = r.json()["id"]
    r = client.post(f"/api/v1/discipline/{incident_id}/notify-parent", headers=admin_h)
    assert r.status_code == 200 and r.json()["notified"] >= 1
    # SMS logged with the event code
    log = client.get("/api/v1/communications/sms-log", headers=admin_h,
                     params={"limit": 10}).json()["items"]
    assert any(m["event_code"] == "DISCIPLINE_NOTICE" for m in log)
    # guardian login received the in-app notice
    parent_h = auth_headers(login(client, "parentU"))
    notifs = client.get("/api/v1/communications/notifications", headers=parent_h).json()["items"]
    assert any(n["kind"] == "DISCIPLINE_NOTICE" for n in notifs)


def test_unauthorized_roles_blocked(client, ids):
    p_h = auth_headers(login(client, "parentU"))
    assert client.post("/api/v1/discipline", headers=p_h, json={
        "student_id": str(ids["st1"]), "category": "OTHER",
        "description": "attempt by parent"}).status_code == 403
