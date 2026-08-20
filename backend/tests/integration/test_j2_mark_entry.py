"""Journey J2: teacher login → assigned class → enter marks → submit → lock (spec §45)."""
from tests.conftest import auth_headers, login


def _component_ids(client, term_id, stream_id, subject_id):
    r = client.get("/api/v1/assessments/sheets", params={
        "term_id": term_id, "class_stream_id": stream_id, "subject_id": subject_id})
    assert r.status_code == 200, r.text
    return {c["code"]: c["id"] for c in r.json()["components"]}


def _sheet(client, csrf, term_id, stream_id, subject_id, component_id):
    r = client.get("/api/v1/assessments/sheets", params={
        "term_id": term_id, "class_stream_id": stream_id, "subject_id": subject_id,
        "component_id": component_id})
    assert r.status_code == 200, r.text
    return r.json()["sheet"]


def test_j2_full_journey(client, ids):
    teacher = login(client, "teacherA")
    h = auth_headers(teacher)

    # roster → enrollment ids for B1A (teacher sees own class via scoped students API)
    roster = client.get(f"/api/v1/classes/streams/{ids['stream_b1a']}/roster")
    codes = [i["admission_code"] for i in roster.json()["items"]]
    assert {"THSA-0001", "THSA-0002"} <= set(codes)

    enr = client.get("/api/v1/students", params={"class_stream_id": str(ids["stream_b1a"])})
    st_ids = [i["id"] for i in enr.json()["items"]]
    enrollments = []
    for sid in st_ids:
        e = client.get(f"/api/v1/students/{sid}/enrollments").json()["items"]
        enrollments.append(next(x for x in e if x["status"] == "ACTIVE")["id"])
    assert len(enrollments) >= 2  # roster may grow as earlier journeys enroll students

    # components come from the configured scheme (50/50 as config rows, not code)
    comps = _component_ids(client, ids["term1"], ids["stream_b1a"], ids["subject_eng"])
    assert set(comps) == {"CLASS_SCORE", "TERMINAL_EXAM"}

    # enter class scores
    sheet = _sheet(client, teacher, ids["term1"], ids["stream_b1a"],
                   ids["subject_eng"], comps["CLASS_SCORE"])
    assert sheet["status"] == "DRAFT"
    entries = [{"enrollment_id": e, "raw_score": 78 + (i % 4) * 5}
               for i, e in enumerate(enrollments)]
    r = client.post("/api/v1/assessments/sheets/scores", headers=h,
                    json={"sheet_id": sheet["id"], "entries": entries})
    assert r.status_code == 200, r.text
    assert r.json()["saved"] == len(enrollments)

    # out-of-range score rejected (BR-M06)
    bad = client.post("/api/v1/assessments/sheets/scores", headers=h,
                      json={"sheet_id": sheet["id"],
                            "entries": [{"enrollment_id": enrollments[0], "raw_score": 140}]})
    assert bad.status_code == 409 and bad.json()["error"]["code"] == "SCORE_OUT_OF_RANGE"

    # completeness is enforced by default: the roster may hold thousands of
    # students (soak tests), so scoring only ours is "incomplete"
    r = client.post("/api/v1/assessments/sheets/submit", headers=h,
                    json={"sheet_id": sheet["id"]})
    assert r.status_code == 409 and r.json()["error"]["code"] == "SHEET_INCOMPLETE"
    r = client.post("/api/v1/assessments/sheets/submit", headers=h,
                    json={"sheet_id": sheet["id"], "allow_incomplete": True})
    assert r.status_code == 200

    # after submission, silent edits are impossible (BR-M03)
    r = client.post("/api/v1/assessments/sheets/scores", headers=h,
                    json={"sheet_id": sheet["id"],
                          "entries": [{"enrollment_id": enrollments[0], "raw_score": 99}]})
    assert r.status_code == 423
    assert r.json()["error"]["code"] == "MARKS_LOCKED"

    # teacher cannot lock (needs OVERRIDE_MARKS) — head can
    r = client.post("/api/v1/assessments/sheets/lock", headers=h,
                    json={"sheet_id": sheet["id"]})
    assert r.status_code == 403

    from tests.conftest import login as li
    head_csrf = li(client, "head")
    r = client.post("/api/v1/assessments/sheets/lock", headers=auth_headers(head_csrf),
                    json={"sheet_id": sheet["id"]})
    assert r.status_code == 200 and r.json()["status"] == "LOCKED"


def test_teacher_cannot_enter_unassigned_class(client, ids):
    """teacherB has no B1A assignment → every access path denied (J8 core)."""
    csrf = login(client, "teacherB")
    h = auth_headers(csrf)
    enr = client.get("/api/v1/students", params={"class_stream_id": str(ids["stream_b1a"])})
    # scoped list returns nothing for teacherB in someone else's class
    assert enr.json()["items"] == []

    # sheet discovery for the unassigned class is denied before any component is revealed
    r = client.get("/api/v1/assessments/sheets", params={
        "term_id": ids["term1"], "class_stream_id": ids["stream_b1a"],
        "subject_id": ids["subject_eng"]})
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "NOT_ASSIGNED_CLASS"


def test_subject_scoped_assignment(client, ids):
    """teacherA is ENG-only in B2A: ENG allowed, MAT denied (REQ-MRK-01)."""
    csrf = login(client, "teacherA")
    r = client.get("/api/v1/assessments/sheets", params={
        "term_id": ids["term1"], "class_stream_id": ids["stream_b2a"],
        "subject_id": ids["subject_eng"]})
    assert r.status_code == 200
    r = client.get("/api/v1/assessments/sheets", params={
        "term_id": ids["term1"], "class_stream_id": ids["stream_b2a"],
        "subject_id": ids["subject_mat"]})
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "NOT_ASSIGNED_SUBJECT"
