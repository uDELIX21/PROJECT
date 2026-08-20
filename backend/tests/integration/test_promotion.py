"""End-of-year promotion workflow (REQ-STU-03/04, BR-S05/06)."""
from tests.conftest import auth_headers, login


def test_promotion_preview_and_apply(client, ids):
    csrf = login(client, "admin")
    h = auth_headers(csrf)
    payload = {"from_academic_year_id": str(ids["year_cur"]),
               "to_academic_year_id": str(ids["year_next"]),
               "decisions": []}

    # preview lists all active students with suggested decisions
    pv = client.post("/api/v1/enrollments/promotion/preview", headers=h, json=payload)
    assert pv.status_code == 200, pv.text
    items = pv.json()["items"]
    assert len(items) >= 3
    assert all(i["suggested_decision"] in ("PROMOTE", "GRADUATE") for i in items)

    # missing decisions → blocked (no silent skips, BR-S05)
    bad = client.post("/api/v1/enrollments/promotion/apply", headers=h, json=payload)
    assert bad.status_code == 409 and bad.json()["error"]["code"] == "DECISION_MISSING"

    # explicit decision for every student; JHS3 student graduates
    decisions = [{"student_id": i["student_id"],
                  "decision": i["suggested_decision"]} for i in items]
    ok = client.post("/api/v1/enrollments/promotion/apply", headers=h,
                     json={**payload, "decisions": decisions})
    assert ok.status_code == 200, ok.text

    # old enrollments completed; promoted students now enrolled in the next year.
    # (The listing endpoint caps at 500/page, so verify structurally instead of
    # by exact count: sample students + capped listing.)
    listing = client.get("/api/v1/enrollments",
                         params={"academic_year_id": str(ids["year_next"]), "limit": 500})
    next_rows = listing.json()["items"]
    promotes = [d for d in decisions if d["decision"] == "PROMOTE"]
    assert len(next_rows) == min(len(promotes), 500)
    sample = next(d for d in decisions if d["decision"] == "PROMOTE")
    enr = client.get(f"/api/v1/students/{sample['student_id']}/enrollments").json()["items"]
    assert any(e["academic_year_id"] == str(ids["year_next"]) and e["status"] == "ACTIVE"
               for e in enr)

    # re-applying the same batch is rejected
    again = client.post("/api/v1/enrollments/promotion/apply", headers=h,
                        json={**payload, "decisions": decisions})
    assert again.status_code == 409 and again.json()["error"]["code"] == "BATCH_EXISTS"


def test_graduate_only_jhs3(client, ids):
    """Self-contained: enrolls a fresh Basic-1 student, then forces GRADUATE (BR-S06)."""
    csrf = login(client, "admin")
    h = auth_headers(csrf)
    r = client.post("/api/v1/students", headers=h, json={
        "surname": "Gradcheck", "other_names": "Junior", "gender": "M",
        "date_of_birth": "2019-06-06", "admit": True})
    sid = r.json()["id"]
    r = client.post("/api/v1/enrollments", headers=h, json={
        "student_id": sid, "class_stream_id": str(ids["stream_b1a"])})
    assert r.status_code == 201, r.text

    # dedicated year pair: no previously applied batch can shadow the validation
    pv = client.post("/api/v1/enrollments/promotion/preview", headers=h, json={
        "from_academic_year_id": str(ids["year_cur"]),
        "to_academic_year_id": str(ids["year_next2"]), "decisions": []})
    items = pv.json()["items"]
    item = next(i for i in items if i["student_id"] == sid)
    assert item["suggested_decision"] == "PROMOTE"  # Basic 1 — never graduate
    decisions = [{"student_id": i["student_id"],
                  "decision": "GRADUATE" if i["student_id"] == sid else "PROMOTE"}
                 for i in items]
    r = client.post("/api/v1/enrollments/promotion/apply", headers=h, json={
        "from_academic_year_id": str(ids["year_cur"]),
        "to_academic_year_id": str(ids["year_next2"]),
        "decisions": decisions})
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "GRADUATE_INVALID"
