"""Attendance module: sheets, summaries, compliance, scoping (REQ-ATT-*)."""
from datetime import date

from tests.conftest import auth_headers, login


def _enrollments(client, stream_id):
    st = client.get("/api/v1/students", params={"class_stream_id": str(stream_id)}).json()["items"]
    out = []
    for s in st:
        e = client.get(f"/api/v1/students/{s['id']}/enrollments").json()["items"]
        out.append(next(x for x in e if x["status"] == "ACTIVE")["id"])
    return out


def test_sheet_save_submit_summary(client, ids):
    csrf = login(client, "teacherA")
    h = auth_headers(csrf)
    enr = _enrollments(client, ids["stream_b1a"])
    day = date(2026, 9, 14)  # Monday within Term 1

    r = client.put("/api/v1/attendance/sheets", headers=h, json={
        "class_stream_id": str(ids["stream_b1a"]), "term_id": str(ids["term1"]),
        "sheet_date": str(day),
        "records": [{"enrollment_id": enr[0], "status": "PRESENT"},
                    {"enrollment_id": enr[1], "status": "LATE", "note": "traffic"}]})
    assert r.status_code == 200, r.text
    sheet_id = r.json()["id"]

    # invalid status rejected at the validation layer
    bad = client.put("/api/v1/attendance/sheets", headers=h, json={
        "class_stream_id": str(ids["stream_b1a"]), "term_id": str(ids["term1"]),
        "sheet_date": str(day),
        "records": [{"enrollment_id": enr[0], "status": "HALF_DAY"}]})
    assert bad.status_code == 422 and bad.json()["error"]["code"] == "VALIDATION_FAILED"

    # submit
    r = client.post("/api/v1/attendance/sheets/submit", headers=h, json={"sheet_id": sheet_id})
    assert r.status_code == 200 and r.json()["status"] == "SUBMITTED"

    # edits after submit blocked (BR-T04)
    again = client.put("/api/v1/attendance/sheets", headers=h, json={
        "class_stream_id": str(ids["stream_b1a"]), "term_id": str(ids["term1"]),
        "sheet_date": str(day),
        "records": [{"enrollment_id": enr[0], "status": "ABSENT"}]})
    assert again.status_code == 423

    # class summary: 1 present + 1 late → both weighted 1.0 → 100%
    s = client.get("/api/v1/attendance/summary", params={
        "class_stream_id": str(ids["stream_b1a"]), "term_id": str(ids["term1"])}).json()
    assert len(s["items"]) == 2
    assert all(i["percentage"] == 100.0 for i in s["items"])
    late = next(i for i in s["items"] if i["counts"].get("LATE"))
    assert late["counts"]["LATE"] == 1


def test_teacher_scoped_to_assigned_classes(client, ids):
    csrf = login(client, "teacherB")
    h = auth_headers(csrf)
    day = date(2026, 9, 15)
    r = client.put("/api/v1/attendance/sheets", headers=h, json={
        "class_stream_id": str(ids["stream_b1a"]), "term_id": str(ids["term1"]),
        "sheet_date": str(day), "records": []})
    assert r.status_code == 404  # uniform: teacherB has no B1A assignment

    view = client.get("/api/v1/attendance/sheets", params={
        "class_stream_id": str(ids["stream_b1a"]), "sheet_date": "2026-09-14"})
    assert view.status_code == 404


def test_date_outside_term_rejected(client, ids):
    csrf = login(client, "teacherA")
    r = client.put("/api/v1/attendance/sheets", headers=auth_headers(csrf), json={
        "class_stream_id": str(ids["stream_b1a"]), "term_id": str(ids["term1"]),
        "sheet_date": "2027-06-01", "records": []})
    assert r.status_code == 409 and r.json()["error"]["code"] == "DATE_OUT_OF_TERM"


def test_compliance_report(client, ids):
    csrf = login(client, "head")
    r = client.get("/api/v1/attendance/compliance", params={"term_id": str(ids["term1"])})
    assert r.status_code == 200
    items = r.json()["items"]
    assert items, "expected one row per class stream"
    row = next(i for i in items if i["class_name"].startswith("Basic 1"))
    assert row["expected_days"] > 0
    assert row["compliance_pct"] is not None
