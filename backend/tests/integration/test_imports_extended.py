"""Extended import coverage (spec §44 Import Tests): XLSX files, teacher &
parent imports, large-file soak, permission edges."""
import io

from tests.conftest import auth_headers, login


def _xlsx(rows: list[list]) -> bytes:
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    for r in rows:
        ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_xlsx_student_import(client, ids):
    h = auth_headers(login(client, "admin"))
    data = _xlsx([
        ["admission_code", "surname", "other_names", "gender", "date_of_birth", "class",
         "guardian_name", "guardian_relationship", "guardian_phone", "guardian_email",
         "guardian_address", "ghana_digital_address", "opening_balance_ghs"],
        ["", "Xlsx", "Kid", "F", "2018-08-08", "Basic 1 A", "Xlsx Mother", "MOTHER",
         "0206667777", "", "", "", "50.00"],
    ])
    r = client.post("/api/v1/imports/upload", headers=h,
                    files={"file": ("students.xlsx", data,
                                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                    data={"kind": "STUDENTS"})
    assert r.status_code == 201, r.text
    assert r.json()["rows_ok"] == 1
    job = r.json()["job_id"]
    ok = client.post(f"/api/v1/imports/{job}/confirm", headers=h)
    assert ok.status_code == 200 and ok.json()["created"] == 1
    kids = client.get("/api/v1/students?q=Xlsx").json()["items"]
    assert any(k["full_name"] == "Xlsx Kid" for k in kids)
    alpha = next(k for k in kids if k["full_name"] == "Xlsx Kid")
    assert client.get(f"/api/v1/fees/balances?student_id={alpha['id']}") \
        .json()["balance_pesewas"] == 5000


def test_teacher_import_with_assignments(client, ids):
    h = auth_headers(login(client, "admin"))
    csv_text = """staff_code,surname,other_names,gender,phone,email,job_title,qualification,hired_on,primary_class,assigned_subjects
T-900,Imported,Teacher,M,0207778899,t900@example.com,Teacher,B.Ed,2023-01-09,Basic 1 A,MAT;SCI
"""
    r = client.post("/api/v1/imports/upload", headers=h,
                    files={"file": ("teachers.csv", io.BytesIO(csv_text.encode()), "text/csv")},
                    data={"kind": "TEACHERS"})
    assert r.json()["rows_ok"] == 1, r.text
    job = r.json()["job_id"]
    ok = client.post(f"/api/v1/imports/{job}/confirm", headers=h)
    assert ok.status_code == 200 and ok.json()["created"] == 1
    # teacher exists with form + subject assignments
    all_t = client.get("/api/v1/teachers?limit=100").json()["items"]
    t = next(x for x in all_t if x["full_name"] == "Imported Teacher")
    assigns = client.get(f"/api/v1/teachers/{t['id']}/assignments").json()["items"]
    roles = {a["role"] for a in assigns}
    assert "FORM_TEACHER" in roles and "SUBJECT_TEACHER" in roles


def test_parent_import_links_by_admission_code(client, ids):
    h = auth_headers(login(client, "admin"))
    # use an existing student's code (THSA-0001)
    csv_text = """name,relationship_to,student_admission_code,student_name,phone,phone2,email,occupation,residential_address,ghana_digital_address,latitude,longitude,preferred_channel,contact_window
Parent Import,GRANDPARENT,THSA-0001,,0208889900,,,,,,,,"",""
"""
    r = client.post("/api/v1/imports/upload", headers=h,
                    files={"file": ("parents.csv", io.BytesIO(csv_text.encode()), "text/csv")},
                    data={"kind": "PARENTS"})
    assert r.status_code == 201, r.text
    job = r.json()["job_id"]
    ok = client.post(f"/api/v1/imports/{job}/confirm", headers=h)
    assert ok.status_code == 200 and ok.json()["created"] == 1
    guardians = client.get(f"/api/v1/students/{ids['st1']}/guardians").json()["items"]
    assert any(g["parent"]["name"] == "Parent Import" for g in guardians)


def test_large_file_soak_5000_rows(client, ids):
    """5,000-row import parses, previews and commits without corruption."""
    h = auth_headers(login(client, "admin"))
    import random
    rng = random.Random(99)
    lines = ["admission_code,surname,other_names,gender,date_of_birth,class,guardian_name,guardian_relationship,guardian_phone,guardian_email,guardian_address,ghana_digital_address,opening_balance_ghs"]
    classes = ["Basic 1 A", "Basic 2 A"]  # streams that exist in the fixture school
    for i in range(5000):
        balance = "25.00" if i % 7 == 0 else ""
        lines.append(f",Soak,S{i},{'F' if i % 2 else 'M'},2017-01-{(i % 28) + 1:02d},"
                     f"{classes[i % len(classes)]},,,,,,,"
                     f"{balance}")
    csv_text = "\n".join(lines)
    r = client.post("/api/v1/imports/upload", headers=h,
                    files={"file": ("soak.csv", io.BytesIO(csv_text.encode()), "text/csv")},
                    data={"kind": "STUDENTS"})
    assert r.status_code == 201, r.text
    assert r.json()["rows_total"] == 5000
    assert r.json()["rows_ok"] == 5000
    job = r.json()["job_id"]
    ok = client.post(f"/api/v1/imports/{job}/confirm", headers=h)
    assert ok.status_code == 200, ok.text
    assert ok.json()["created"] == 5000
    rep = client.get(f"/api/v1/imports/{job}").json()
    assert rep["stage"] == "COMPLETED"


def test_query_plans_use_indexes_on_hot_paths(client, ids):
    """Performance guard (REQ-LOW-01): hot queries must not full-scan."""
    from sqlalchemy import text
    from app.core.db import get_engine
    eng = get_engine()
    sid = str(ids["st1"])
    queries = [
        f"EXPLAIN QUERY PLAN SELECT * FROM ledger_entries WHERE student_id = '{sid}'",
        f"EXPLAIN QUERY PLAN SELECT * FROM ledger_entries WHERE student_id = '{sid}' AND term_id IS NULL",
        f"EXPLAIN QUERY PLAN SELECT * FROM fee_charges WHERE student_id = '{sid}' AND status = 'ACTIVE'",
        f"EXPLAIN QUERY PLAN SELECT * FROM enrollments WHERE academic_year_id = '{ids['year_cur']}' AND status = 'ACTIVE'",
    ]
    with eng.connect() as conn:
        for q in queries:
            rows = conn.execute(text(q)).fetchall()
            plan_text = " ".join(str(r) for r in rows)
            # SQLite: index use shows as "SEARCH ... USING INDEX"; a bare
            # "SCAN <table>" (without USING INDEX) means a full scan
            assert "USING INDEX" in plan_text or "USING COVERING INDEX" in plan_text, \
                f"full scan detected: {plan_text}"
