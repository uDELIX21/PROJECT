"""Bulk import journey (spec §45 CSV import): upload → validate → preview →
confirm → report; duplicates, malformed rows, parent match confirmation,
transaction safety."""
import io

from tests.conftest import auth_headers, login

STUDENTS_CSV = """admission_code,surname,other_names,gender,date_of_birth,class,guardian_name,guardian_relationship,guardian_phone,guardian_email,guardian_address,ghana_digital_address,opening_balance_ghs
,Imported,Alpha,F,2018-05-01,Basic 1 A,Alpha Mother,MOTHER,0201112233,alpha@example.com,1 Test Rd,GA-111-2222,120.50
,Imported,Beta,M,12/04/2017,Basic 1 A,Beta Father,FATHER,0204455667,,2 Test Rd,,
"""


def _upload(client, h, csv_text, kind="STUDENTS"):
    return client.post("/api/v1/imports/upload", headers=h,
                       files={"file": ("students.csv", io.BytesIO(csv_text.encode()), "text/csv")},
                       data={"kind": kind})


def test_template_download(client, ids):
    h = auth_headers(login(client, "admin"))
    r = client.get("/api/v1/imports/templates/STUDENTS?format=csv")
    assert r.status_code == 200
    first_line = r.content.decode("utf-8-sig").splitlines()[0]
    assert "surname" in first_line and "opening_balance_ghs" in first_line
    x = client.get("/api/v1/imports/templates/STUDENTS?format=xlsx")
    assert x.status_code == 200 and x.content[:2] == b"PK"


def test_student_import_full_journey(client, ids):
    h = auth_headers(login(client, "admin"))
    r = _upload(client, h, STUDENTS_CSV)
    assert r.status_code == 201, r.text
    body = r.json()
    job_id = body["job_id"]
    assert body["rows_total"] == 2 and body["rows_ok"] == 2

    # preview shows the parsed rows
    pv = client.get(f"/api/v1/imports/{job_id}/preview").json()
    assert pv["job"]["stage"] == "PREVIEWED"
    assert len(pv["rows"]) == 2

    students_before = client.get("/api/v1/students?q=Imported").json()["items"]
    n_before = len(students_before)

    # confirm → atomic commit
    r = client.post(f"/api/v1/imports/{job_id}/confirm", headers=h)
    assert r.status_code == 200, r.text
    assert r.json()["created"] == 2

    students_after = client.get("/api/v1/students?q=Imported").json()["items"]
    assert len(students_after) == n_before + 2
    alpha = next(s for s in students_after if s["full_name"] == "Imported Alpha")
    beta = next(s for s in students_after if s["full_name"] == "Imported Beta")

    # enrolled into Basic 1 A
    enr = client.get(f"/api/v1/students/{alpha['id']}/enrollments").json()["items"]
    assert enr and enr[0]["stream_name"] == "Basic 1 A"

    # guardian created + linked
    g = client.get(f"/api/v1/students/{alpha['id']}/guardians").json()["items"]
    assert g and g[0]["parent"]["name"] == "Alpha Mother"
    assert g[0]["parent"]["phone"] == "+233201112233"

    # opening balance posted to the ledger (120.50 GHS)
    bal = client.get(f"/api/v1/fees/balances?student_id={alpha['id']}").json()
    assert bal["balance_pesewas"] == 12050
    assert any(e["category"] == "OPENING_BALANCE" for e in bal["entries"])

    # report + history
    rep = client.get(f"/api/v1/imports/{job_id}").json()
    assert rep["stage"] == "COMPLETED" and rep["summary"]["created"] == 2
    hist = client.get("/api/v1/imports").json()["items"]
    assert any(j["id"] == job_id for j in hist)


def test_malformed_rows_block_commit_and_save_nothing(client, ids):
    h = auth_headers(login(client, "admin"))
    bad_csv = """admission_code,surname,other_names,gender,date_of_birth,class,guardian_name,guardian_relationship,guardian_phone
,Broken,Row,XYZ,not-a-date,Basic 99 Z,,,
"""
    r = _upload(client, h, bad_csv)
    body = r.json()
    assert body["rows_error"] == 1
    job_id = body["job_id"]
    pv = client.get(f"/api/v1/imports/{job_id}/preview?severity=ERROR").json()
    row = pv["rows"][0]
    assert "gender" in row["message"] or "date" in row["message"]
    # every issue is reported, incl. the unknown class with suggestion guidance
    assert "No class 'Basic 99 Z'" in row["message"]
    assert row["guidance"]  # correction guidance present

    before = client.get("/api/v1/students?q=Broken").json()["items"]
    r = client.post(f"/api/v1/imports/{job_id}/confirm", headers=h)
    assert r.status_code == 409 and r.json()["error"]["code"] == "ERRORS_BLOCK_COMMIT"
    after = client.get("/api/v1/students?q=Broken").json()["items"]
    assert len(after) == len(before)  # nothing saved


def test_duplicates_detected_and_skipped(client, ids):
    h = auth_headers(login(client, "admin"))
    # duplicate within file + duplicate against DB (THSA-0001 exists from fixture)
    csv_text = """admission_code,surname,other_names,gender,date_of_birth,class,guardian_name,guardian_relationship,guardian_phone
,Dupkid,One,F,2019-01-01,Basic 1 A,,,
,Dupkid,One,F,2019-01-01,Basic 1 A,,,
THSA-0001,Existing,Child,M,2019-02-02,Basic 1 A,,,
"""
    r = _upload(client, h, csv_text)
    body = r.json()
    assert body["rows_duplicate"] >= 2, body
    job_id = body["job_id"]
    r = client.post(f"/api/v1/imports/{job_id}/confirm", headers=h)
    assert r.status_code == 200
    # row 1 imports; row 2 (in-file dup) + row 3 (matches THSA-0001) are skipped
    assert r.json()["skipped_duplicates"] == 2
    assert r.json()["created"] == 1
    dup_after = client.get("/api/v1/students?q=Dupkid").json()["items"]
    assert len(dup_after) == 1  # exactly one Dupkid, no doubles


def test_parent_phone_match_requires_confirmation(client, ids):
    """Agent Rule 8: phone matches are suggestions only — confirmed by a human."""
    h = auth_headers(login(client, "admin"))
    # parentU's guardian phone is +233241234567 (fixture)
    csv_text = """admission_code,surname,other_names,gender,date_of_birth,class,guardian_name,guardian_relationship,guardian_phone
,Matchkid,Child,F,2019-03-03,Basic 1 A,Owusu Guardian,MOTHER,0241234567
"""
    r = _upload(client, h, csv_text)
    body = r.json()
    assert body["rows_match"] == 1, body
    job_id = body["job_id"]

    # confirm WITHOUT resolving the match → blocked
    r = client.post(f"/api/v1/imports/{job_id}/confirm", headers=h)
    assert r.status_code == 409 and r.json()["error"]["code"] == "MATCHES_UNRESOLVED"

    # inspect the candidate and confirm the LINK
    pv = client.get(f"/api/v1/imports/{job_id}/preview?severity=MATCH_CANDIDATE").json()
    row = pv["rows"][0]
    candidate = row["match_suggestion"]["candidates"][0]
    assert candidate["guardian_name"] == "Owusu Guardian"
    assert candidate["confidence"] in ("high", "very high")
    r = client.post(f"/api/v1/imports/{job_id}/matches/{row['id']}/resolve", headers=h,
                    json={"action": "LINK", "guardian_id": candidate["guardian_id"]})
    assert r.status_code == 200

    # now commit succeeds and links the EXISTING guardian (no duplicate created)
    r = client.post(f"/api/v1/imports/{job_id}/confirm", headers=h)
    assert r.status_code == 200 and r.json()["created"] == 1

    kids = client.get("/api/v1/students?q=Matchkid").json()["items"]
    g = client.get(f"/api/v1/students/{kids[0]['id']}/guardians").json()["items"]
    assert len(g) == 1
    assert g[0]["parent"]["name"] == "Owusu Guardian"
    assert g[0]["source"] == "IMPORT_SUGGESTION"
    assert g[0]["parent"]["id"] == candidate["guardian_id"]

    # link confirmation is audited
    audit = client.get("/api/v1/audit", params={"action": "import.match_resolved"}).json()["items"]
    assert audit and audit[0]["new"]["action"] == "LINK"


def test_unreadable_file_fails_job(client, ids):
    h = auth_headers(login(client, "admin"))
    r = client.post("/api/v1/imports/upload", headers=h,
                    files={"file": ("bad.bin", io.BytesIO(b"\x00\x01\x02garbage"), "text/csv")},
                    data={"kind": "STUDENTS"})
    assert r.status_code in (201, 409)  # parsed as zero/odd rows or failed cleanly
    r2 = client.post("/api/v1/imports/upload", headers=h,
                     files={"file": ("evil.exe", io.BytesIO(b"MZ"), "application/octet-stream")},
                     data={"kind": "STUDENTS"})
    assert r2.status_code == 409 and r2.json()["error"]["code"] == "FILE_TYPE_INVALID"


def test_import_permission_guard(client, ids):
    h = auth_headers(login(client, "teacherA"))
    r = _upload(client, h, STUDENTS_CSV)
    assert r.status_code == 403
