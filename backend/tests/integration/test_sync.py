"""Offline sync endpoint (journey J9 server side): idempotent replays, version
conflicts, scoping, validation — mutations land exactly once."""
import uuid

from tests.conftest import auth_headers, login


def _sheet_for_b1a(client, ids, subject_key, comp="CLASS_SCORE"):
    """Sheets for subjects untouched by other journeys (ENG/MAT are submitted by J2/J3)."""
    subj = ids[subject_key]
    comps = client.get("/api/v1/assessments/sheets", params={
        "term_id": str(ids["term1"]), "class_stream_id": str(ids["stream_b1a"]),
        "subject_id": str(subj)}).json()["components"]
    comp_id = next(c["id"] for c in comps if c["code"] == comp)
    sheet = client.get("/api/v1/assessments/sheets", params={
        "term_id": str(ids["term1"]), "class_stream_id": str(ids["stream_b1a"]),
        "subject_id": str(subj), "component_id": comp_id}).json()["sheet"]
    return sheet, comp_id


def _fresh_b1a_enrollments(client, ids, h, n=2):
    """Create fresh students enrolled in B1A — unaffected by promotion runs
    that completed the seeded enrollments."""
    out = []
    for i in range(n):
        r = client.post("/api/v1/students", headers=h, json={
            "surname": f"Synckid{subject_suffix()}", "other_names": f"Num{i}",
            "gender": "F", "date_of_birth": "2018-03-03", "admit": True})
        sid = r.json()["id"]
        r = client.post("/api/v1/enrollments", headers=h, json={
            "student_id": sid, "class_stream_id": str(ids["stream_b1a"])})
        assert r.status_code == 201, r.text
        out.append(r.json()["id"])
    return out


def subject_suffix():
    import random
    return str(random.randint(1000, 9999))


def test_sync_applies_and_is_idempotent(client, ids):
    admin_h = auth_headers(login(client, "admin"))  # fixtures need EDIT_STUDENT
    enr = _fresh_b1a_enrollments(client, ids, admin_h)
    h = auth_headers(login(client, "teacherA"))     # sync runs as the teacher
    sheet, comp_id = _sheet_for_b1a(client, ids, "subject_sci")
    mid = str(uuid.uuid4())

    body = {"mutations": [{"client_mutation_id": mid, "entity_type": "ASSESSMENT_SCORE",
                           "entity_ref": f"assessment={sheet['id']};enrollment={enr[0]}",
                           "base_version": sheet["version"],
                           "payload": {"assessment_id": sheet["id"],
                                       "enrollment_id": enr[0], "raw_score": 77}}]}
    r1 = client.post("/api/v1/sync/mutations", headers=h, json=body)
    assert r1.status_code == 200, r1.text
    res = r1.json()["results"][0]
    assert res["status"] == "APPLIED" and res["replayed"] is False
    new_version = res["result"]["server_version"]

    # verify the score exists via the sheet view
    view = client.get("/api/v1/assessments/sheets", params={
        "term_id": str(ids["term1"]), "class_stream_id": str(ids["stream_b1a"]),
        "subject_id": str(ids["subject_sci"]), "component_id": comp_id}).json()
    score = next(s for s in view["scores"] if s["enrollment_id"] == enr[0])
    assert score["raw_score"] == 77.0

    # replay: identical mutation → stored result, applied exactly once
    r2 = client.post("/api/v1/sync/mutations", headers=h, json=body)
    res2 = r2.json()["results"][0]
    assert res2["status"] == "APPLIED" and res2["replayed"] is True
    view2 = client.get("/api/v1/assessments/sheets", params={
        "term_id": str(ids["term1"]), "class_stream_id": str(ids["stream_b1a"]),
        "subject_id": str(ids["subject_sci"]), "component_id": comp_id}).json()
    assert view2["sheet"]["version"] == new_version  # unchanged by replay

    # batch with a mix: one new + one replay
    mid2 = str(uuid.uuid4())
    mixed = {"mutations": [
        body["mutations"][0],
        {"client_mutation_id": mid2, "entity_type": "ASSESSMENT_SCORE",
         "base_version": new_version,
         "payload": {"assessment_id": sheet["id"], "enrollment_id": enr[1],
                     "raw_score": 88}}]}
    r3 = client.post("/api/v1/sync/mutations", headers=h, json=mixed)
    statuses = {x["client_mutation_id"]: x for x in r3.json()["results"]}
    assert statuses[mid]["replayed"] is True
    assert statuses[mid2]["status"] == "APPLIED" and statuses[mid2]["replayed"] is False


def test_sync_version_conflict_reports_server_value(client, ids):
    admin_h = auth_headers(login(client, "admin"))
    enr = _fresh_b1a_enrollments(client, ids, admin_h)
    h = auth_headers(login(client, "teacherA"))
    sheet, comp_id = _sheet_for_b1a(client, ids, "subject_sci")

    # teacher's offline copy is stale: bump the sheet server-side first
    ok = client.post("/api/v1/assessments/sheets/scores", headers=h, json={
        "sheet_id": sheet["id"],
        "entries": [{"enrollment_id": enr[0], "raw_score": 50}]})
    assert ok.status_code == 200

    stale = {"mutations": [{
        "client_mutation_id": str(uuid.uuid4()), "entity_type": "ASSESSMENT_SCORE",
        "base_version": sheet["version"],  # stale
        "payload": {"assessment_id": sheet["id"], "enrollment_id": enr[0],
                    "raw_score": 99}}]}
    r = client.post("/api/v1/sync/mutations", headers=h, json=stale)
    res = r.json()["results"][0]
    assert res["status"] == "CONFLICT"
    assert res["result"]["code"] == "VERSION_CONFLICT"
    assert res["result"]["details"]["server_value"] == 50.0

    # server value untouched by the conflicted mutation
    view = client.get("/api/v1/assessments/sheets", params={
        "term_id": str(ids["term1"]), "class_stream_id": str(ids["stream_b1a"]),
        "subject_id": str(ids["subject_sci"]), "component_id": comp_id}).json()
    score = next(s for s in view["scores"] if s["enrollment_id"] == enr[0])
    assert score["raw_score"] == 50.0


def test_sync_scoping_and_validation(client, ids):
    admin_h = auth_headers(login(client, "admin"))
    enr = _fresh_b1a_enrollments(client, ids, admin_h)
    sheet, comp_id = _sheet_for_b1a(client, ids, "subject_sci")
    # teacherB has no B1A assignment → REJECTED, not applied
    h_b = auth_headers(login(client, "teacherB"))

    denied = {"mutations": [{
        "client_mutation_id": str(uuid.uuid4()), "entity_type": "ASSESSMENT_SCORE",
        "payload": {"assessment_id": sheet["id"], "enrollment_id": enr[0],
                    "raw_score": 60}}]}
    r = client.post("/api/v1/sync/mutations", headers=h_b, json=denied)
    res = r.json()["results"][0]
    assert res["status"] == "REJECTED"
    assert res["result"]["code"] == "NOT_ASSIGNED_CLASS"

    h_a = auth_headers(login(client, "teacherA"))  # re-login: cookie was swapped
    # out-of-range score rejected with the same envelope
    bad = {"mutations": [{
        "client_mutation_id": str(uuid.uuid4()), "entity_type": "ASSESSMENT_SCORE",
        "payload": {"assessment_id": sheet["id"], "enrollment_id": enr[0],
                    "raw_score": 500}}]}
    r = client.post("/api/v1/sync/mutations", headers=h_a, json=bad)
    assert r.json()["results"][0]["result"]["code"] == "SCORE_OUT_OF_RANGE"

    # submitted sheets refuse offline writes too (BR-M03)
    client.post("/api/v1/assessments/sheets/scores", headers=h_a, json={
        "sheet_id": sheet["id"],
        "entries": [{"enrollment_id": enr[0], "raw_score": 70},
                    {"enrollment_id": enr[1], "raw_score": 71}]})
    client.post("/api/v1/assessments/sheets/submit", headers=h_a,
                json={"sheet_id": sheet["id"], "allow_incomplete": True})
    locked = {"mutations": [{
        "client_mutation_id": str(uuid.uuid4()), "entity_type": "ASSESSMENT_SCORE",
        "payload": {"assessment_id": sheet["id"], "enrollment_id": enr[0],
                    "raw_score": 75}}]}
    r = client.post("/api/v1/sync/mutations", headers=h_a, json=locked)
    assert r.json()["results"][0]["result"]["code"] == "MARKS_LOCKED"


def test_sync_attendance_records(client, ids):
    admin_h = auth_headers(login(client, "admin"))
    enr = _fresh_b1a_enrollments(client, ids, admin_h)
    h = auth_headers(login(client, "teacherA"))
    day = "2026-09-21"  # Monday in Term 1

    batch = {"mutations": [
        {"client_mutation_id": str(uuid.uuid4()), "entity_type": "ATTENDANCE_RECORD",
         "payload": {"class_stream_id": str(ids["stream_b1a"]),
                     "term_id": str(ids["term1"]), "sheet_date": day,
                     "enrollment_id": enr[0], "status": "PRESENT"}},
        {"client_mutation_id": str(uuid.uuid4()), "entity_type": "ATTENDANCE_RECORD",
         "payload": {"class_stream_id": str(ids["stream_b1a"]),
                     "term_id": str(ids["term1"]), "sheet_date": day,
                     "enrollment_id": enr[1], "status": "LATE", "note": "bus delay"}}]}
    r = client.post("/api/v1/sync/mutations", headers=h, json=batch)
    assert all(x["status"] == "APPLIED" for x in r.json()["results"]), r.text

    view = client.get("/api/v1/attendance/sheets", params={
        "class_stream_id": str(ids["stream_b1a"]), "sheet_date": day}).json()
    by_enr = {rec["enrollment_id"]: rec for rec in view["records"]}
    assert by_enr[enr[0]]["status"] == "PRESENT"
    assert by_enr[enr[1]]["status"] == "LATE"

    # teacherB cannot sync attendance for B1A
    h_b = auth_headers(login(client, "teacherB"))
    denied = {"mutations": [{
        "client_mutation_id": str(uuid.uuid4()), "entity_type": "ATTENDANCE_RECORD",
        "payload": {"class_stream_id": str(ids["stream_b1a"]),
                    "term_id": str(ids["term1"]), "sheet_date": day,
                    "enrollment_id": enr[0], "status": "ABSENT"}}]}
    r = client.post("/api/v1/sync/mutations", headers=h_b, json=denied)
    assert r.json()["results"][0]["result"]["code"] == "NOT_ASSIGNED_CLASS"


def test_sync_requires_enter_marks_permission(client, ids):
    h = auth_headers(login(client, "parentU"))
    r = client.post("/api/v1/sync/mutations", headers=h, json={"mutations": [{
        "client_mutation_id": str(uuid.uuid4()), "entity_type": "ASSESSMENT_SCORE",
        "payload": {}}]})
    assert r.status_code == 403
