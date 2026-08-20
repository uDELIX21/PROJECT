"""Sync mixed-batch behaviour (design §09): per-mutation independence —
one failure never blocks the rest; every verdict is reported and recorded."""
import uuid

from tests.conftest import auth_headers, login


def test_mixed_batch_partial_success(client, ids):
    h = auth_headers(login(client, "teacherA"))
    # fixture sheet (B1A ENG CLASS_SCORE) via admin-free flow: teacher owns B1A form
    comps = client.get("/api/v1/assessments/sheets", params={
        "term_id": str(ids["term1"]), "class_stream_id": str(ids["stream_b1a"]),
        "subject_id": str(ids["subject_eng"])}).json()["components"]
    comp_id = next(c["id"] for c in comps if c["code"] == "CLASS_SCORE")
    sheet = client.get("/api/v1/assessments/sheets", params={
        "term_id": str(ids["term1"]), "class_stream_id": str(ids["stream_b1a"]),
        "subject_id": str(ids["subject_eng"]), "component_id": comp_id}).json()["sheet"]
    if sheet["status"] != "DRAFT":
        import pytest
        pytest.skip("sheet already submitted by another test")
    roster = client.get(f"/api/v1/classes/streams/{ids['stream_b1a']}/roster").json()["items"]
    enr = roster[0]["enrollment"]["id"]

    good_id = str(uuid.uuid4())
    bad_id = str(uuid.uuid4())
    batch = {"mutations": [
        {"client_mutation_id": good_id, "entity_type": "ASSESSMENT_SCORE",
         "base_version": sheet["version"],
         "payload": {"assessment_id": sheet["id"], "enrollment_id": enr,
                     "raw_score": 71}},
        {"client_mutation_id": bad_id, "entity_type": "ASSESSMENT_SCORE",
         "payload": {"assessment_id": "00000000-0000-0000-0000-000000000000",
                     "enrollment_id": enr, "raw_score": 71}},
        {"client_mutation_id": str(uuid.uuid4()), "entity_type": "NOT_A_TYPE",
         "payload": {}},
    ]}
    r = client.post("/api/v1/sync/mutations", headers=h, json=batch)
    assert r.status_code == 200
    results = {x["client_mutation_id"]: x for x in r.json()["results"]}
    assert results[good_id]["status"] == "APPLIED"
    assert results[bad_id]["status"] == "REJECTED"
    assert results[bad_id]["result"]["code"] == "NOT_FOUND"
    unknown = [x for x in r.json()["results"]
               if x["client_mutation_id"] not in (good_id, bad_id)][0]
    assert unknown["status"] == "REJECTED"
    assert unknown["result"]["code"] == "MUTATION_TYPE_UNKNOWN"

    # the good mutation persisted despite its batch-mates failing
    view = client.get("/api/v1/assessments/sheets", params={
        "term_id": str(ids["term1"]), "class_stream_id": str(ids["stream_b1a"]),
        "subject_id": str(ids["subject_eng"]), "component_id": comp_id}).json()
    score = next(s for s in view["scores"] if s["enrollment_id"] == enr)
    assert score["raw_score"] == 71.0

    # replay of the same batch: stored verdicts, nothing re-applied
    r2 = client.post("/api/v1/sync/mutations", headers=h, json=batch)
    results2 = {x["client_mutation_id"]: x for x in r2.json()["results"]}
    assert results2[good_id]["replayed"] is True
    view2 = client.get("/api/v1/assessments/sheets", params={
        "term_id": str(ids["term1"]), "class_stream_id": str(ids["stream_b1a"]),
        "subject_id": str(ids["subject_eng"]), "component_id": comp_id}).json()
    assert view2["sheet"]["version"] == view["sheet"]["version"]  # unchanged
