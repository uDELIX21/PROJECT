"""Student registry API: CRUD, validation, lifecycle transitions, audit trail."""
from tests.conftest import auth_headers, login


def _create(client, csrf, surname="Testey", other="Newbie", admit=True):
    r = client.post("/api/v1/students", headers=auth_headers(csrf), json={
        "surname": surname, "other_names": other, "gender": "F",
        "date_of_birth": "2019-05-04", "admit": admit})
    assert r.status_code == 201, r.text
    return r.json()


def test_create_student_generates_admission_code(client, ids):
    csrf = login(client, "admin")
    s = _create(client, csrf)
    assert s["admission_code"].startswith("THSA-")
    assert s["status"] == "ADMITTED"


def test_duplicate_admission_code_impossible(client, ids):
    csrf = login(client, "admin")
    a = _create(client, csrf, surname="One")
    b = _create(client, csrf, surname="Two")
    assert a["admission_code"] != b["admission_code"]


def test_validation_errors_use_envelope(client, ids):
    csrf = login(client, "admin")
    r = client.post("/api/v1/students", headers=auth_headers(csrf), json={
        "surname": "  ", "other_names": "X", "gender": "F",
        "date_of_birth": "2019-05-04"})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "VALIDATION_FAILED"


def test_status_transition_rules(client, ids):
    csrf = login(client, "admin")
    s = _create(client, csrf, surname="Transit", admit=False)  # APPLICANT
    sid = s["id"]
    # illegal: APPLICANT -> GRADUATED
    bad = client.post(f"/api/v1/students/{sid}/status", headers=auth_headers(csrf),
                      json={"status": "GRADUATED"})
    assert bad.status_code == 409
    assert bad.json()["error"]["code"] == "ILLEGAL_TRANSITION"
    # legal: APPLICANT -> ADMITTED
    ok = client.post(f"/api/v1/students/{sid}/status", headers=auth_headers(csrf),
                     json={"status": "ADMITTED", "reason": "board approved"})
    assert ok.status_code == 200
    assert ok.json()["status"] == "ADMITTED"


def test_biodata_change_is_audited(client, ids):
    csrf = login(client, "admin")
    s = _create(client, csrf, surname="Auditee")
    r = client.patch(f"/api/v1/students/{s['id']}", headers=auth_headers(csrf),
                     json={"surname": "Audited-Name"})
    assert r.status_code == 200
    assert r.json()["surname"] == "Audited-Name"
    audit = client.get("/api/v1/audit", params={
        "entity_type": "student", "entity_id": s["id"], "action": "student.biodata_changed"})
    assert audit.status_code == 200
    items = audit.json()["items"]
    assert len(items) == 1
    assert items[0]["previous"]["surname"] == "Auditee"
    assert items[0]["new"]["surname"] == "Audited-Name"


def test_parent_scope_only_own_children(client, ids):
    csrf = login(client, "parentU")
    # own child visible
    ok = client.get(f"/api/v1/students/{ids['st1']}")
    assert ok.status_code == 200
    # another family's child is a uniform 404 (REQ-PRV-02)
    hidden = client.get(f"/api/v1/students/{ids['st3']}")
    assert hidden.status_code == 404
    # list shows linked children (st1, st2 + any siblings added by other tests,
    # e.g. confirmed import matches) — but never another family's child
    listing = client.get("/api/v1/students")
    codes = {i["admission_code"] for i in listing.json()["items"]}
    assert {"THSA-0001", "THSA-0002"} <= codes
    assert "THSA-0003" not in codes
