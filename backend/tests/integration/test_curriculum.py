"""Curriculum engine: versioning, tree, publish-time immutability (REQ-CUR-*, BR-C)."""
from tests.conftest import auth_headers, login


def test_curriculum_lifecycle_and_immutability(client, ids):
    csrf = login(client, "admin")
    h = auth_headers(csrf)

    # create curriculum + draft version
    r = client.post("/api/v1/curriculum", headers=h, json={
        "name": "NaCCA Basic School Curriculum", "origin": "NATIONAL"})
    assert r.status_code == 201
    cur_id = r.json()["id"]
    r = client.post("/api/v1/curriculum/versions", headers=h, json={
        "curriculum_id": cur_id, "version_label": "2026.v1"})
    assert r.status_code == 201
    v1 = r.json()["id"]

    # build a small tree: B1 Mathematics → Numbers → Counting → standard → indicator
    grade_b1, subj_mat = str(ids["grades"]["B1"]), str(ids["subject_mat"])
    r = client.post(f"/api/v1/curriculum/versions/{v1}/strands", headers=h, json={
        "grade_id": grade_b1, "subject_id": subj_mat, "code": "S1", "title": "Numbers"})
    strand_id = r.json()["id"]
    r = client.post(f"/api/v1/curriculum/strands/{strand_id}/sub-strands", headers=h,
                    json={"code": "S1.1", "title": "Counting and representation"})
    sub_id = r.json()["id"]
    r = client.post(f"/api/v1/curriculum/sub-strands/{sub_id}/content-standards", headers=h,
                    json={"code": "S1.1.1", "title": "Count objects up to 100"})
    cs_id = r.json()["id"]
    r = client.post(f"/api/v1/curriculum/content-standards/{cs_id}/indicators", headers=h,
                    json={"code": "B1.1.1.1", "title": "Count forwards and backwards to 100"})
    assert r.status_code == 201

    tree = client.get(f"/api/v1/curriculum/versions/{v1}/tree",
                      params={"grade_id": grade_b1, "subject_id": subj_mat}).json()["items"]
    assert tree[0]["title"] == "Numbers"
    assert tree[0]["sub_strands"][0]["content_standards"][0]["indicators"][0]["code"] == "B1.1.1.1"

    # publish → freeze (BR-C01)
    r = client.post(f"/api/v1/curriculum/versions/{v1}/publish", headers=h)
    assert r.status_code == 200 and r.json()["status"] == "PUBLISHED"

    blocked = client.post(f"/api/v1/curriculum/versions/{v1}/strands", headers=h, json={
        "grade_id": grade_b1, "subject_id": subj_mat, "code": "S9", "title": "Late addition"})
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "VERSION_IMMUTABLE"

    # new version copies the tree (history preserved, evolution possible)
    r = client.post("/api/v1/curriculum/versions", headers=h, json={
        "curriculum_id": cur_id, "version_label": "2027.v1", "copy_from_version_id": v1})
    v2 = r.json()["id"]
    tree2 = client.get(f"/api/v1/curriculum/versions/{v2}/tree",
                       params={"grade_id": grade_b1, "subject_id": subj_mat}).json()["items"]
    assert tree2[0]["title"] == "Numbers"
    # …and the draft accepts edits again
    r = client.post(f"/api/v1/curriculum/versions/{v2}/strands", headers=h, json={
        "grade_id": grade_b1, "subject_id": subj_mat, "code": "S9", "title": "New strand"})
    assert r.status_code == 201


def test_competency_catalog(client, ids):
    csrf = login(client, "head")
    r = client.get("/api/v1/curriculum/competencies")
    codes = {c["code"] for c in r.json()["items"]}
    assert {"CRITICAL_THINKING", "CREATIVITY", "COMMUNICATION", "COLLABORATION",
            "DIGITAL_LITERACY", "PROBLEM_SOLVING"} <= codes


def test_curriculum_write_requires_permission(client, ids):
    csrf = login(client, "teacherA")
    r = client.post("/api/v1/curriculum", headers=auth_headers(csrf),
                    json={"name": "Teacher curriculum"})
    assert r.status_code == 403
    # read is allowed for teachers (VIEW_GRADES_CONFIG)
    assert client.get("/api/v1/curriculum").status_code == 200
