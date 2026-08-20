"""Report cards: generation, PDF, finalization, publication, access scoping (REQ-RPT-*)."""
from tests.conftest import auth_headers, login


def _b1a_map(client, ids):
    """student_id → enrollment id for B1A (any status — a promotion batch applied by
    an earlier test may have COMPLETED these enrollments; reports still render them)."""
    rows = client.get("/api/v1/enrollments", params={
        "class_stream_id": str(ids["stream_b1a"]), "status": ""}).json()["items"]
    out = {}
    for e in rows:
        out[e["student_id"]] = e["id"]
    return out


def _fill_scores(client, h, ids, mapping):
    """Ensure ENG + MAT have scores for B1A (only touches DRAFT sheets — submitted
    sheets from earlier journey tests stay untouched, which is exactly BR-M03)."""
    for subject in (ids["subject_eng"], ids["subject_mat"]):
        comps = client.get("/api/v1/assessments/sheets", params={
            "term_id": str(ids["term1"]), "class_stream_id": str(ids["stream_b1a"]),
            "subject_id": str(subject)}).json()["components"]
        for code, vals in (("CLASS_SCORE", (74, 88)), ("TERMINAL_EXAM", (66, 92))):
            comp_id = next(c["id"] for c in comps if c["code"] == code)
            view = client.get("/api/v1/assessments/sheets", params={
                "term_id": str(ids["term1"]), "class_stream_id": str(ids["stream_b1a"]),
                "subject_id": str(subject), "component_id": comp_id}).json()
            if view["sheet"]["status"] != "DRAFT":
                continue  # already submitted/locked by J2/J3 — scores already present
            entries = [{"enrollment_id": enr, "raw_score": vals[i % 2]}
                       for i, enr in enumerate(mapping.values())]
            r = client.post("/api/v1/assessments/sheets/scores", headers=h, json={
                "sheet_id": view["sheet"]["id"], "entries": entries})
            assert r.status_code == 200


def test_primary_report_lifecycle_and_pdf(client, ids):
    csrf = login(client, "admin")
    h = auth_headers(csrf)
    mapping = _b1a_map(client, ids)
    _fill_scores(client, h, ids, mapping)
    student_id = str(ids["st1"])  # parentU's child — publication scoping checks below
    assert student_id in mapping

    # generate
    r = client.post("/api/v1/reports/generate", headers=h, json={
        "student_id": student_id, "term_id": str(ids["term1"]),
        "teacher_remark": "A focused learner.", "head_remark": "Promoted to Basic 2."})
    assert r.status_code == 201, r.text
    report_id = r.json()["id"]
    assert r.json()["status"] == "GENERATED"

    # PDF downloads (staff)
    pdf = client.get(f"/api/v1/reports/{report_id}/pdf")
    assert pdf.status_code == 200
    assert pdf.headers["content-type"].startswith("application/pdf")
    assert pdf.content[:5] == b"%PDF-"
    assert len(pdf.content) > 1500

    # golden assertions: extract text and verify key content survived rendering
    import io
    from pypdf import PdfReader
    text = "\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(pdf.content)).pages)
    assert "Hope Star" in text  # school name
    assert "Terminal Report" in text
    assert "English Language" in text
    assert "Attendance" in text
    assert "A focused learner." in text

    # parent cannot see unpublished reports (BR-R04)
    login(client, "parentU")
    listing = client.get("/api/v1/reports", params={
        "term_id": str(ids["term1"]), "student_id": student_id})
    assert listing.status_code == 200 and listing.json()["items"] == []
    pdf2 = client.get(f"/api/v1/reports/{report_id}/pdf")
    assert pdf2.status_code == 404  # uniform — existence not leaked

    # finalize → publish → parent access granted (fresh admin session → fresh CSRF)
    h = auth_headers(login(client, "admin"))
    r = client.post(f"/api/v1/reports/{report_id}/finalize", headers=h)
    assert r.status_code == 200
    r = client.post(f"/api/v1/reports/{report_id}/publish", headers=h, json={})
    assert r.status_code == 200
    assert r.json()["clearance"]["state"] == "CLEAR"  # Phase-4 stub (Phase 5 enforces fees)

    login(client, "parentU")
    listing = client.get("/api/v1/reports", params={
        "term_id": str(ids["term1"]), "student_id": student_id})
    assert len(listing.json()["items"]) == 1
    # unscoped listing must also be child-scoped — parentU links st1+st2, and other
    # tests may publish sibling reports, but never another family's (st3)
    unscoped = client.get("/api/v1/reports", params={"term_id": str(ids["term1"])})
    items = unscoped.json()["items"]
    assert all(r["student_id"] in (str(ids["st1"]), str(ids["st2"])) for r in items)
    assert any(r["student_id"] == student_id for r in items)
    pdf3 = client.get(f"/api/v1/reports/{report_id}/pdf")
    assert pdf3.status_code == 200

    # regeneration after finalization blocked (BR-R03)
    h = auth_headers(login(client, "admin"))
    r = client.post("/api/v1/reports/generate", headers=h, json={
        "student_id": student_id, "term_id": str(ids["term1"])})
    assert r.status_code == 409 and r.json()["error"]["code"] == "REPORT_FINALIZED"


def test_parent_of_other_child_cannot_read_report(client, ids):
    """parentU links st1+st2 only; st3 (another family) must stay hidden."""
    csrf = login(client, "admin")
    h = auth_headers(csrf)
    mapping = _b1a_map(client, ids)
    _fill_scores(client, h, ids, mapping)
    st3 = str(ids["st3"])
    # st3 is in B2A; enroll scores there via a direct report generate (needs scheme → B2 has one)
    enr3 = client.get(f"/api/v1/students/{st3}/enrollments").json()["items"]
    enr3_id = next(x for x in enr3 if x["status"] == "ACTIVE")["id"]
    comps = client.get("/api/v1/assessments/sheets", params={
        "term_id": str(ids["term1"]), "class_stream_id": str(ids["stream_b2a"]),
        "subject_id": str(ids["subject_eng"])}).json()["components"]
    comp_id = next(c["id"] for c in comps if c["code"] == "CLASS_SCORE")
    view = client.get("/api/v1/assessments/sheets", params={
        "term_id": str(ids["term1"]), "class_stream_id": str(ids["stream_b2a"]),
        "subject_id": str(ids["subject_eng"]), "component_id": comp_id}).json()
    if view["sheet"]["status"] == "DRAFT":
        client.post("/api/v1/assessments/sheets/scores", headers=h, json={
            "sheet_id": view["sheet"]["id"],
            "entries": [{"enrollment_id": enr3_id, "raw_score": 60}]})
    r = client.post("/api/v1/reports/generate", headers=h, json={
        "student_id": st3, "term_id": str(ids["term1"])})
    assert r.status_code == 201, r.text
    report_id = r.json()["id"]
    client.post(f"/api/v1/reports/{report_id}/publish", headers=h, json={})

    login(client, "parentU")
    forbidden = client.get(f"/api/v1/reports/{report_id}/pdf")
    assert forbidden.status_code == 404  # uniform: not leaked as 403


def test_ecd_report_renders_developmental_grid(client, ids):
    csrf = login(client, "admin")
    h = auth_headers(csrf)
    r = client.post("/api/v1/students", headers=h, json={
        "surname": "Reportchild", "other_names": "Afia", "gender": "F",
        "date_of_birth": "2022-07-07", "admit": True})
    sid = r.json()["id"]
    r = client.post("/api/v1/enrollments", headers=h, json={
        "student_id": sid, "class_stream_id": str(ids["stream_kg1a"])})
    enr_id = r.json()["id"]
    domains = client.get("/api/v1/ecd/domains").json()["items"]
    client.put("/api/v1/ecd/ratings", headers=h, json={
        "enrollment_id": enr_id, "term_id": str(ids["term1"]),
        "ratings": [{"domain_id": domains[0]["id"], "rating": "EMERGING"},
                    {"domain_id": domains[1]["id"], "rating": "ACHIEVED"}]})
    client.post("/api/v1/ecd/observations", headers=h, json={
        "enrollment_id": enr_id, "body": "Enjoys painting sessions."})

    r = client.post("/api/v1/reports/generate", headers=h, json={
        "student_id": sid, "term_id": str(ids["term1"])})
    assert r.status_code == 201, r.text
    pdf = client.get(f"/api/v1/reports/{r.json()['id']}/pdf")
    assert pdf.status_code == 200 and pdf.content[:5] == b"%PDF-"

    import io
    from pypdf import PdfReader
    text = "\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(pdf.content)).pages)
    assert "Developmental Assessment" in text
    assert "Enjoys painting sessions." in text
    # ECD report must not contain a numeric academic subject table
    assert "English Language" not in text


def test_templates_are_configurable(client, ids):
    csrf = login(client, "admin")
    h = auth_headers(csrf)
    templates = client.get("/api/v1/reports/templates").json()["items"]
    assert {t["band"] for t in templates} == {"EARLY_CHILDHOOD", "PRIMARY", "JHS"}
    primary = next(t for t in templates if t["band"] == "PRIMARY")
    r = client.put(f"/api/v1/reports/templates/{primary['id']}", headers=h, json={
        "layout_config": {**primary["layout_config"], "show_positions": False}})
    assert r.status_code == 200
    assert r.json()["layout_config"]["show_positions"] is False
