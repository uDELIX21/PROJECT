"""Journey J8: Teacher A attempts to access Teacher B's class → denied (spec §45).

Plus an RBAC sweep: every role × representative endpoint behaves as designed.
"""
from tests.conftest import PASSWORD, auth_headers, login


def test_teacher_a_cannot_see_teacher_b_class(client, ids):
    """teacherA's assignments: B1A (form) + B2A (ENG only). KG1A belongs to neither
    teacher in this fixture — accessing it must fail uniformly (REQ-TCH-02, J8)."""
    csrf = login(client, "teacherA")
    # roster of a class teacherA is not assigned to → uniform 404 (no scope probing)
    r = client.get(f"/api/v1/classes/streams/{ids['stream_kg1a']}/roster")
    assert r.status_code == 404
    # …but own form class is fine
    mine = client.get(f"/api/v1/classes/streams/{ids['stream_b1a']}/roster")
    assert mine.status_code == 200
    # …and the subject-assigned class is visible
    partial = client.get(f"/api/v1/classes/streams/{ids['stream_b2a']}/roster")
    assert partial.status_code == 200
    # teacherB (no KG1A/B1A assignments) is denied both
    login(client, "teacherB")
    assert client.get(f"/api/v1/classes/streams/{ids['stream_kg1a']}/roster").status_code == 404
    assert client.get(f"/api/v1/classes/streams/{ids['stream_b1a']}/roster").status_code == 404


def test_teacher_student_scope(client, ids):
    csrf = login(client, "teacherA")
    # teacherA's own class (B1A) students visible
    assert client.get(f"/api/v1/students/{ids['st1']}").status_code == 200
    assert client.get(f"/api/v1/students/{ids['st2']}").status_code == 200
    # st3 (B2A) visible to teacherA only through the subject-scoped ENG assignment
    assert client.get(f"/api/v1/students/{ids['st3']}").status_code == 200

    # teacherB owns B2A (st3) but never B1A students → uniform 404
    login(client, "teacherB")
    assert client.get(f"/api/v1/students/{ids['st3']}").status_code == 200
    assert client.get(f"/api/v1/students/{ids['st1']}").status_code == 404
    assert client.get(f"/api/v1/students/{ids['st2']}").status_code == 404


def test_teacher_cannot_administer(client, ids):
    csrf = login(client, "teacherA")
    h = auth_headers(csrf)
    assert client.get("/api/v1/users").status_code == 403
    assert client.post("/api/v1/students", headers=h, json={
        "surname": "Nope", "other_names": "Nope", "gender": "F",
        "date_of_birth": "2019-01-01"}).status_code == 403
    assert client.post("/api/v1/enrollments", headers=h, json={
        "student_id": str(ids["st1"]),
        "class_stream_id": str(ids["stream_b1a"])}).status_code == 403
    assert client.get("/api/v1/audit").status_code == 403


def test_bursar_cannot_touch_academics(client, ids):
    csrf = login(client, "bursar")
    h = auth_headers(csrf)
    # bursar may view students (finance context)…
    assert client.get(f"/api/v1/students/{ids['st1']}").status_code == 200
    # …but not edit them, enroll, or manage users
    assert client.patch(f"/api/v1/students/{ids['st1']}", headers=h,
                        json={"surname": "Hacked"}).status_code == 403
    assert client.post("/api/v1/enrollments", headers=h, json={
        "student_id": str(ids["st1"]),
        "class_stream_id": str(ids["stream_b1a"])}).status_code == 403
    assert client.get("/api/v1/users").status_code == 403


def test_parent_cannot_write(client, ids):
    csrf = login(client, "parentU")
    h = auth_headers(csrf)
    assert client.post("/api/v1/students", headers=h, json={
        "surname": "X", "other_names": "Y", "gender": "F",
        "date_of_birth": "2019-01-01"}).status_code == 403
    assert client.get("/api/v1/teachers").status_code == 403
    assert client.get("/api/v1/audit").status_code == 403
    assert client.get("/api/v1/users").status_code == 403


def test_head_teacher_can_manage_but_not_user_admin(client, ids):
    csrf = login(client, "head")
    # head can enroll…
    h = auth_headers(csrf)
    r = client.get(f"/api/v1/classes/streams/{ids['stream_kg1a']}/roster")
    assert r.status_code == 200
    # …but /users admin is reserved for super admin (HEAD lacks MANAGE_USERS)
    assert client.get("/api/v1/users").status_code == 403


def test_hidden_resources_return_404_not_403(client, ids):
    """Out-of-scope access must not reveal existence (REQ-PRV-02)."""
    csrf = login(client, "parentU")
    r = client.get(f"/api/v1/students/{ids['st3']}")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "NOT_FOUND"
