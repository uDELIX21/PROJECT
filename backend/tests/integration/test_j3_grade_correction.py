"""Journey J3: teacher requests correction → admin reviews → override → audit (spec §45)."""
from tests.conftest import auth_headers, login


def test_j3_correction_workflow(client, ids):
    from fastapi.testclient import TestClient
    from app.main import app
    admin_client = TestClient(app)  # separate session jar: admin stays logged in
    admin_csrf = login(admin_client, "admin")
    ah = auth_headers(admin_csrf)
    teacher_csrf = login(client, "teacherA")  # owns B1A as form teacher
    th = auth_headers(teacher_csrf)

    # fixtures: enrollments in B1A + a submitted CLASS_SCORE sheet for MAT
    st = client.get("/api/v1/students", params={"class_stream_id": str(ids["stream_b1a"])}).json()["items"]
    enr_ids = []
    for s in st:
        e = client.get(f"/api/v1/students/{s['id']}/enrollments").json()["items"]
        enr_ids.append(next(x for x in e if x["status"] == "ACTIVE")["id"])

    comps = client.get("/api/v1/assessments/sheets", params={
        "term_id": str(ids["term1"]), "class_stream_id": str(ids["stream_b1a"]),
        "subject_id": str(ids["subject_mat"])}).json()["components"]
    comp_id = next(c["id"] for c in comps if c["code"] == "CLASS_SCORE")
    sheet = client.get("/api/v1/assessments/sheets", params={
        "term_id": str(ids["term1"]), "class_stream_id": str(ids["stream_b1a"]),
        "subject_id": str(ids["subject_mat"]), "component_id": comp_id}).json()["sheet"]

    teacher_csrf = login(client, "teacherA")
    th = auth_headers(teacher_csrf)
    r = client.post("/api/v1/assessments/sheets/scores", headers=th, json={
        "sheet_id": sheet["id"],
        "entries": [{"enrollment_id": e, "raw_score": 55 + (i % 4) * 8}
                    for i, e in enumerate(enr_ids)]})
    assert r.status_code == 200
    r = client.post("/api/v1/assessments/sheets/submit", headers=th,
                    json={"sheet_id": sheet["id"], "allow_incomplete": True})
    assert r.status_code == 200

    # locate the score row for student 1
    sheet_view = client.get("/api/v1/assessments/sheets", params={
        "term_id": str(ids["term1"]), "class_stream_id": str(ids["stream_b1a"]),
        "subject_id": str(ids["subject_mat"]), "component_id": comp_id}).json()
    score_row = next(s for s in sheet_view["scores"] if s["enrollment_id"] == enr_ids[0])
    assert score_row["raw_score"] == 55.0

    # 1. teacher requests correction with reason
    r = client.post("/api/v1/assessments/corrections", headers=th, json={
        "assessment_score_id": score_row["id"], "new_score": 65,
        "reason": "Quiz 2 was mis-totalled; re-checked against exercise book."})
    assert r.status_code == 201, r.text
    override_id = r.json()["id"]

    # duplicate pending request blocked
    dup = client.post("/api/v1/assessments/corrections", headers=th, json={
        "assessment_score_id": score_row["id"], "new_score": 70, "reason": "again"})
    assert dup.status_code == 409

    # 2. teacher cannot self-approve
    r = client.post(f"/api/v1/assessments/corrections/{override_id}/resolve", headers=th,
                    json={"approve": True})
    assert r.status_code == 403

    # 3. admin approves → score updated
    r = admin_client.post(f"/api/v1/assessments/corrections/{override_id}/resolve", headers=ah,
                          json={"approve": True})
    assert r.status_code == 200

    sheet_view = client.get("/api/v1/assessments/sheets", params={
        "term_id": str(ids["term1"]), "class_stream_id": str(ids["stream_b1a"]),
        "subject_id": str(ids["subject_mat"]), "component_id": comp_id}).json()
    score_row = next(s for s in sheet_view["scores"] if s["enrollment_id"] == enr_ids[0])
    assert score_row["raw_score"] == 65.0

    # 4. audit trail carries original → new + reason (BR-M04)
    audit = admin_client.get("/api/v1/audit", params={
        "action": "correction.approved", "entity_type": "assessment_score"}).json()["items"]
    hit = next(a for a in audit if a["entity_id"] == score_row["id"])
    assert hit["previous"]["raw_score"] == 55.0
    assert hit["new"]["raw_score"] == 65.0
    assert "mis-totalled" in hit["reason"]

    # 5. rejection path leaves score untouched
    r = client.post("/api/v1/assessments/corrections", headers=th, json={
        "assessment_score_id": score_row["id"], "new_score": 99,
        "reason": "please bump for good behaviour"})
    ov2 = r.json()["id"]
    r = admin_client.post(f"/api/v1/assessments/corrections/{ov2}/resolve", headers=ah,
                          json={"approve": False})
    assert r.status_code == 200 and r.json()["status"] == "REJECTED"
    sheet_view = client.get("/api/v1/assessments/sheets", params={
        "term_id": str(ids["term1"]), "class_stream_id": str(ids["stream_b1a"]),
        "subject_id": str(ids["subject_mat"]), "component_id": comp_id}).json()
    score_row = next(s for s in sheet_view["scores"] if s["enrollment_id"] == enr_ids[0])
    assert score_row["raw_score"] == 65.0  # unchanged
