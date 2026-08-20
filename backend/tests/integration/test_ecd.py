"""Early-childhood developmental assessment (REQ-ECD-*, BR-E)."""
from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import auth_headers, login


def _kg1_enrollment(admin_client, ids):
    """Enroll a fresh student into KG1A (early childhood band)."""
    csrf = login(admin_client, "admin")
    h = auth_headers(csrf)
    r = admin_client.post("/api/v1/students", headers=h, json={
        "surname": "Ecdchild", "other_names": "Kukua", "gender": "F",
        "date_of_birth": "2022-03-03", "admit": True})
    sid = r.json()["id"]
    r = admin_client.post("/api/v1/enrollments", headers=h, json={
        "student_id": sid, "class_stream_id": str(ids["stream_kg1a"])})
    assert r.status_code == 201, r.text
    return sid, r.json()["id"]


def test_domains_catalog_seeded(client, ids):
    login(client, "teacherA")
    r = client.get("/api/v1/ecd/domains")
    codes = {d["code"] for d in r.json()["items"]}
    assert {"GROSS_MOTOR", "FINE_MOTOR", "LANGUAGE", "COGNITIVE", "SOCIAL",
            "EMOTIONAL", "SELF_CARE", "CREATIVITY"} <= codes


def test_ratings_and_observations(client, ids):
    admin_client = TestClient(app)
    sid, enr_id = _kg1_enrollment(admin_client, ids)
    ah = auth_headers(login(admin_client, "admin"))

    domains = admin_client.get("/api/v1/ecd/domains").json()["items"]
    d_motor = next(d for d in domains if d["code"] == "GROSS_MOTOR")
    d_lang = next(d for d in domains if d["code"] == "LANGUAGE")

    # teacherA is not assigned to KG1 → write scoping denies (uniform 404)
    teacher_client = TestClient(app)
    th = auth_headers(login(teacher_client, "teacherA"))
    scoped = teacher_client.put("/api/v1/ecd/ratings", headers=th, json={
        "enrollment_id": enr_id, "term_id": str(ids["term1"]),
        "ratings": [{"domain_id": d_motor["id"], "rating": "ACHIEVED"}]})
    assert scoped.status_code == 404

    # admin (unscoped staff) applies the ratings
    r = admin_client.put("/api/v1/ecd/ratings", headers=ah, json={
        "enrollment_id": enr_id, "term_id": str(ids["term1"]),
        "ratings": [
            {"domain_id": d_motor["id"], "rating": "ACHIEVED", "comment": "Runs confidently"},
            {"domain_id": d_lang["id"], "rating": "DEVELOPING"}]})
    assert r.status_code == 200, r.text

    view = admin_client.get("/api/v1/ecd/ratings", params={
        "enrollment_id": enr_id, "term_id": str(ids["term1"])}).json()
    by_domain = {i["domain"]: i["rating"] for i in view["items"]}
    assert by_domain["Gross Motor Skills"] == "ACHIEVED"
    assert by_domain["Language & Speech"] == "DEVELOPING"

    # invalid rating rejected at the schema layer
    bad = admin_client.put("/api/v1/ecd/ratings", headers=ah, json={
        "enrollment_id": enr_id, "term_id": str(ids["term1"]),
        "ratings": [{"domain_id": d_motor["id"], "rating": "EXCELLENT"}]})
    assert bad.status_code == 422

    # observation log + revision chain (BR-E02)
    r = admin_client.post("/api/v1/ecd/observations", headers=ah, json={
        "enrollment_id": enr_id, "body": "Built a tall block tower, shared toys."})
    assert r.status_code == 201
    obs_id = r.json()["id"]
    r = admin_client.post("/api/v1/ecd/observations", headers=ah, json={
        "enrollment_id": enr_id, "body": "CORRECTION: Built a tall block tower, shared toys well.",
        "supersedes": obs_id})
    assert r.status_code == 201
    view = admin_client.get("/api/v1/ecd/observations",
                            params={"enrollment_id": enr_id}).json()
    assert len(view["items"]) == 1  # superseded note hidden by default
    assert "CORRECTION" in view["items"][0]["body"]
    view_all = admin_client.get("/api/v1/ecd/observations",
                                params={"enrollment_id": enr_id,
                                        "include_superseded": "true"}).json()
    assert len(view_all["items"]) == 2  # history preserved

    # teacher scoped read: KG1 child is invisible to teacherA (uniform 404)
    hidden = teacher_client.get("/api/v1/ecd/ratings", params={
        "enrollment_id": enr_id, "term_id": str(ids["term1"])})
    assert hidden.status_code == 404


def test_non_ecd_class_rejects_developmental_tools(client, ids):
    """BR-M07: ECD tools refuse Basic classes (and schemes refuse KG — see config tests)."""
    csrf = login(client, "admin")
    h = auth_headers(csrf)
    st = client.get("/api/v1/students",
                    params={"class_stream_id": str(ids["stream_b1a"])}).json()["items"]
    e = client.get(f"/api/v1/students/{st[0]['id']}/enrollments").json()["items"]
    enr_b1 = next(x for x in e if x["status"] == "ACTIVE")["id"]
    domains = client.get("/api/v1/ecd/domains").json()["items"]

    r = client.put("/api/v1/ecd/ratings", headers=h, json={
        "enrollment_id": enr_b1, "term_id": str(ids["term1"]),
        "ratings": [{"domain_id": domains[0]["id"], "rating": "ACHIEVED"}]})
    assert r.status_code == 409 and r.json()["error"]["code"] == "NOT_ECD"

    obs = client.post("/api/v1/ecd/observations", headers=h, json={
        "enrollment_id": enr_b1, "body": "should not be allowed"})
    assert obs.status_code == 409 and obs.json()["error"]["code"] == "NOT_ECD"
