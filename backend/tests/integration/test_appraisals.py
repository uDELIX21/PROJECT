"""Teacher appraisal: configurable criteria, evaluator gating, confidentiality,
acknowledgement (REQ-APR-01)."""
from tests.conftest import auth_headers, login


def test_criteria_catalog_and_config(client, ids):
    h = auth_headers(login(client, "head"))
    r = client.get("/api/v1/appraisals/criteria")
    items = r.json()["items"]
    codes = {c["code"] for c in items}
    assert {"LESSON_PLAN_QUALITY", "CLASSROOM_MANAGEMENT", "PUNCTUALITY",
            "SYLLABUS_COMPLETION", "STUDENT_ENGAGEMENT", "PROFESSIONAL_CONDUCT"} <= codes
    # reconfigure a criterion (weight) — config, not code
    crit = next(c for c in items if c["code"] == "PUNCTUALITY")
    r = client.put("/api/v1/appraisals/criteria", headers=h, json={
        "criterion_id": crit["id"], "weight_pct": 25.0})
    assert r.status_code == 200 and r.json()["weight_pct"] == 25.0


def test_appraisal_lifecycle_and_confidentiality(client, ids):
    teacher_id = str(ids["teacherA_profile"])

    # bursar cannot appraise (no APPRAISE_TEACHER)
    bursar_h = auth_headers(login(client, "bursar"))
    r = client.post("/api/v1/appraisals", headers=bursar_h, json={
        "teacher_id": teacher_id, "period_from": "2026-09-07", "period_to": "2026-12-10"})
    assert r.status_code == 403

    # head creates the appraisal (fresh login → matching CSRF)
    head_h = auth_headers(login(client, "head"))
    r = client.post("/api/v1/appraisals", headers=head_h, json={
        "teacher_id": teacher_id, "period_from": "2026-09-07", "period_to": "2026-12-10"})
    assert r.status_code == 201, r.text
    appraisal_id = r.json()["id"]

    criteria = client.get("/api/v1/appraisals/criteria").json()["items"]
    scores = [{"criterion_id": c["id"], "score": 8 if i % 2 else 7,
               "comment": "observed"} for i, c in enumerate(criteria)]
    # out-of-range score rejected
    bad = client.put(f"/api/v1/appraisals/{appraisal_id}/scores", headers=head_h, json={
        "scores": [{"criterion_id": criteria[0]["id"], "score": 999}]})
    assert bad.status_code == 409 and bad.json()["error"]["code"] == "SCORE_OUT_OF_RANGE"

    r = client.put(f"/api/v1/appraisals/{appraisal_id}/scores", headers=head_h,
                   json={"scores": scores})
    assert r.status_code == 200

    # draft is confidential: the appraised teacher cannot see it yet
    ta_h = auth_headers(login(client, "teacherA"))
    hidden = client.get(f"/api/v1/appraisals/{appraisal_id}", headers=ta_h)
    assert hidden.status_code == 404

    head_h = auth_headers(login(client, "head"))  # re-login: cookie was swapped
    r = client.post(f"/api/v1/appraisals/{appraisal_id}/submit", headers=head_h,
                    json={"overall_comment": "Solid term; keep developing assessments."})
    assert r.status_code == 200
    assert r.json()["status"] == "SUBMITTED"
    assert r.json()["overall_rating"] is not None

    # now visible to the teacher, but not to colleagues
    visible = client.get(f"/api/v1/appraisals/{appraisal_id}", headers=ta_h)
    assert visible.status_code == 200
    assert visible.json()["overall_comment"].startswith("Solid term")
    tb_h = auth_headers(login(client, "teacherB"))
    assert client.get(f"/api/v1/appraisals/{appraisal_id}", headers=tb_h).status_code == 404

    # acknowledgement is teacher-only
    denied = client.post(f"/api/v1/appraisals/{appraisal_id}/acknowledge", headers=tb_h)
    assert denied.status_code == 403
    ta_h = auth_headers(login(client, "teacherA"))  # re-login: cookie was swapped
    ack = client.post(f"/api/v1/appraisals/{appraisal_id}/acknowledge", headers=ta_h)
    assert ack.status_code == 200 and ack.json()["status"] == "ACKNOWLEDGED"

    # teacher received an in-app notification on submission
    notifs = client.get("/api/v1/communications/notifications", headers=ta_h).json()["items"]
    assert any(n["kind"] == "APPRAISAL_SUBMITTED" for n in notifs)


def test_overlapping_period_blocked(client, ids):
    h = auth_headers(login(client, "head"))
    body = {"teacher_id": str(ids["teacherB_profile"]),
            "period_from": "2026-09-07", "period_to": "2026-12-10"}
    r1 = client.post("/api/v1/appraisals", headers=h, json=body)
    assert r1.status_code == 201
    criteria = client.get("/api/v1/appraisals/criteria").json()["items"]
    client.put(f"/api/v1/appraisals/{r1.json()['id']}/scores", headers=h,
               json={"scores": [{"criterion_id": criteria[0]["id"], "score": 5}]})
    client.post(f"/api/v1/appraisals/{r1.json()['id']}/submit", headers=h, json={})
    dup = client.post("/api/v1/appraisals", headers=h, json=body)
    assert dup.status_code == 409 and dup.json()["error"]["code"] == "APPRAISAL_OVERLAP"
