"""Journey J1: create student → assign guardian → enroll into class (spec §45)."""
from tests.conftest import auth_headers, login


def test_j1_full_journey(client, ids):
    csrf = login(client, "admin")
    h = auth_headers(csrf)

    # 1. create student (admitted)
    r = client.post("/api/v1/students", headers=h, json={
        "surname": "Journey", "other_names": "Child", "gender": "M",
        "date_of_birth": "2020-02-02", "admit": True})
    assert r.status_code == 201, r.text
    student = r.json()
    assert student["status"] == "ADMITTED"

    # 2. create guardian with Ghana phone normalization
    r = client.post("/api/v1/parents", headers=h, json={
        "name": "Journey Mother", "phone": "0247654321",
        "ghana_digital_address": "GA-456-7890"})
    assert r.status_code == 201, r.text
    guardian = r.json()
    assert guardian["phone"] == "+233247654321"

    # 3. explicit relationship link (multi-child capable)
    r = client.post(f"/api/v1/parents/{guardian['id']}/links", headers=h, json={
        "student_id": student["id"], "relationship_type": "MOTHER",
        "is_primary_contact": True, "is_billing_contact": True})
    assert r.status_code == 201, r.text

    # duplicate link is rejected (never silently merged)
    dup = client.post(f"/api/v1/parents/{guardian['id']}/links", headers=h, json={
        "student_id": student["id"], "relationship_type": "MOTHER"})
    assert dup.status_code == 409 and dup.json()["error"]["code"] == "DUPLICATE_LINK"

    # 4. enroll into Basic 1A (current year inferred from stream)
    r = client.post("/api/v1/enrollments", headers=h, json={
        "student_id": student["id"], "class_stream_id": str(ids["stream_b1a"])})
    assert r.status_code == 201, r.text
    enrollment = r.json()
    assert enrollment["status"] == "ACTIVE"

    # student status advanced to ENROLLED/ACTIVE via lifecycle
    r = client.get(f"/api/v1/students/{student['id']}")
    assert r.json()["status"] in ("ENROLLED", "ACTIVE")

    # 5. student appears on the class roster
    roster = client.get(f"/api/v1/classes/streams/{ids['stream_b1a']}/roster")
    codes = {i["admission_code"] for i in roster.json()["items"]}
    assert student["admission_code"] in codes

    # 6. double enrollment in the same year is rejected (BR-S02)
    again = client.post("/api/v1/enrollments", headers=h, json={
        "student_id": student["id"], "class_stream_id": str(ids["stream_b2a"])})
    assert again.status_code == 409
    assert again.json()["error"]["code"] == "DUPLICATE_ENROLLMENT"

    # 7. guardian's children endpoint reflects the link
    kids = client.get(f"/api/v1/parents/{guardian['id']}/children")
    assert any(k["student"]["id"] == student["id"] for k in kids.json()["items"])

    # 8. enrollment + link are audited
    audit = client.get("/api/v1/audit", params={"action": "enrollment.created"})
    assert any(a["entity_id"] == enrollment["id"] for a in audit.json()["items"])
    audit = client.get("/api/v1/audit", params={"action": "parent.linked"})
    assert audit.json()["items"], "parent linking must be audited (BR-U06)"
