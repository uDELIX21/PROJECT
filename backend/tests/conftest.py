"""Shared fixtures: fresh SQLite DB, seeded catalog + demo people, TestClient."""
import os
import tempfile
from datetime import date, timedelta

# --- env MUST be set before any app import ---
_tmpdir = tempfile.mkdtemp(prefix="sms-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmpdir}/test.db"
os.environ["ARGON_TIME_COST"] = "1"
os.environ["ARGON_MEMORY_COST_KIB"] = "8192"
os.environ["RATELIMIT_ENABLED"] = "false"
os.environ["DEV_MODE"] = "true"

os.environ["SMS_STORAGE_DIR"] = os.path.join(_tmpdir, "storage")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

from app import rbac  # noqa: E402
from app.core import security  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.core.db import get_session_factory  # noqa: E402
from app.core.ids import uuid7  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base  # noqa: E402
from app.models.auth import Role, User, UserRole  # noqa: E402
from app.models.core import (AcademicYear, ClassStream, Enrollment, Grade,  # noqa: E402
                             ParentGuardian, ParentStudentRelationship, School,
                             Student, Teacher, TeacherAssignment, Term)
from app.services import assessment as assess_svc  # noqa: E402
from app.services import catalog, curriculum, grading, reports  # noqa: E402
from app.core.db import get_engine  # noqa: E402

PASSWORD = "Test-Password-99"


def _bootstrap() -> dict:
    """Create schema + catalog + demo users. Returns an id registry for tests."""
    with get_engine().begin() as conn:
        Base.metadata.create_all(conn)
    Session = get_session_factory()
    db = Session()
    ids: dict = {}
    settings = get_settings()

    school = catalog.create_school(db, "Test Hope Star Academy (DEMO)", short_name="THSA",
                                   motto="Test Motto", admission_code_prefix="THSA")
    db.flush()
    departments = catalog.bootstrap_departments(db, school.id)
    catalog.bootstrap_permissions(db)
    roles = catalog.bootstrap_roles(db, school.id)
    grades = catalog.bootstrap_grades(db, school.id, departments)
    catalog.bootstrap_subjects(db, school.id, grades)
    ids["school"] = school.id
    ids["grades"] = {code: g.id for code, g in grades.items()}

    # calendar: previous (closed) + current year w/ active Term 1
    year_prev = AcademicYear(id=uuid7(), school_id=school.id, name="2025/2026",
                             starts_on=date(2025, 9, 8), ends_on=date(2026, 8, 30),
                             status="ARCHIVED")
    year_cur = AcademicYear(id=uuid7(), school_id=school.id, name="2026/2027",
                            starts_on=date(2026, 9, 7), ends_on=date(2027, 8, 29),
                            status="ACTIVE")
    db.add_all([year_prev, year_cur])
    db.flush()
    term1 = Term(id=uuid7(), school_id=school.id, academic_year_id=year_cur.id,
                 name="Term 1", starts_on=date(2026, 9, 7), ends_on=date(2026, 12, 10),
                 status="ACTIVE")
    term2 = Term(id=uuid7(), school_id=school.id, academic_year_id=year_cur.id,
                 name="Term 2", starts_on=date(2027, 1, 6), ends_on=date(2027, 4, 2),
                 status="DRAFT")
    db.add_all([term1, term2])
    db.flush()
    ids.update(year_prev=year_prev.id, year_cur=year_cur.id, term1=term1.id, term2=term2.id)

    # streams for current year: KG1A, B1A, B2A, JHS3A (+ next-year B2A for promotion tests)
    def stream(grade_code: str, year_id, label: str = "A") -> ClassStream:
        g = grades[grade_code]
        s = ClassStream(id=uuid7(), school_id=school.id, grade_id=g.id,
                        academic_year_id=year_id, name=f"{g.name} {label}",
                        section_label=label, capacity=40)
        db.add(s)
        return s

    s_kg1a = stream("KG1", year_cur.id)
    s_b1a = stream("B1", year_cur.id)
    s_b2a = stream("B2", year_cur.id)
    s_jhs3a = stream("JHS3", year_cur.id)
    year_next = AcademicYear(id=uuid7(), school_id=school.id, name="2027/2028",
                             starts_on=date(2027, 9, 6), ends_on=date(2028, 8, 28),
                             status="DRAFT")
    db.add(year_next)
    db.flush()
    s_b2a_next = stream("B2", year_next.id)
    s_b3a_next = stream("B3", year_next.id)
    stream("KG2", year_next.id)   # promotion targets for every enrolled grade
    stream("JHS3", year_next.id)  # repeaters
    # dedicated later year for BR-S06 (graduate-only-JHS3) tests
    year_next2 = AcademicYear(id=uuid7(), school_id=school.id, name="2028/2029",
                              starts_on=date(2028, 9, 4), ends_on=date(2029, 8, 27),
                              status="DRAFT")
    db.add(year_next2)
    db.flush()
    stream("B2", year_next2.id)
    stream("B3", year_next2.id)
    stream("KG2", year_next2.id)
    db.flush()
    ids.update(stream_kg1a=s_kg1a.id, stream_b1a=s_b1a.id, stream_b2a=s_b2a.id,
               stream_jhs3a=s_jhs3a.id, year_next=year_next.id,
               stream_b2a_next=s_b2a_next.id, stream_b3a_next=s_b3a_next.id,
               year_next2=year_next2.id)

    # people
    def make_user(username: str, role_code: str, **links) -> User:
        u = User(id=uuid7(), username=username, display_name=username.title(),
                 password_hash=security.hash_password(PASSWORD, settings), **links)
        db.add(u)
        db.flush()
        db.add(UserRole(user_id=u.id, role_id=roles[role_code].id, granted_by=u.id))
        db.flush()
        return u

    t_a = Teacher(id=uuid7(), school_id=school.id, staff_code="T-A",
                  surname="Amara", other_names="TeacherA")
    t_b = Teacher(id=uuid7(), school_id=school.id, staff_code="T-B",
                  surname="Bonsu", other_names="TeacherB")
    db.add_all([t_a, t_b])
    db.flush()

    ids["admin"] = make_user("admin", rbac.SUPER_ADMIN).id
    ids["head"] = make_user("head", rbac.HEAD_TEACHER).id
    ids["bursar"] = make_user("bursar", rbac.BURSAR).id
    ids["teacherA"] = make_user("teacherA", rbac.TEACHER, teacher_id=t_a.id).id
    ids["teacherB"] = make_user("teacherB", rbac.TEACHER, teacher_id=t_b.id).id
    ids["teacherA_profile"] = t_a.id
    ids["teacherB_profile"] = t_b.id

    # assignments: teacherA → B1A (form), teacherB → B2A (form)
    db.add(TeacherAssignment(id=uuid7(), school_id=school.id, teacher_id=t_a.id,
                             academic_year_id=year_cur.id, class_stream_id=s_b1a.id,
                             role="FORM_TEACHER"))
    db.add(TeacherAssignment(id=uuid7(), school_id=school.id, teacher_id=t_b.id,
                             academic_year_id=year_cur.id, class_stream_id=s_b2a.id,
                             role="FORM_TEACHER"))
    # subject-scoped assignment: teacherA teaches only ENG in B2A (subject boundary tests)
    from app.models.core import Subject as _Subject
    _eng = db.scalar(select(_Subject).where(_Subject.school_id == school.id,
                                            _Subject.code == "ENG"))
    db.add(TeacherAssignment(id=uuid7(), school_id=school.id, teacher_id=t_a.id,
                             academic_year_id=year_cur.id, class_stream_id=s_b2a.id,
                             subject_id=_eng.id, role="SUBJECT_TEACHER"))
    db.flush()

    # students: 2 in B1A (teacherA), 1 in B2A (teacherB), 1 unassigned applicant
    def make_student(code: str, surname: str, other: str, gender: str = "F") -> Student:
        s = Student(id=uuid7(), school_id=school.id, admission_code=code,
                    surname=surname, other_names=other, gender=gender,
                    date_of_birth=date(2019, 3, 12), status="ACTIVE")
        db.add(s)
        return s

    st1 = make_student("THSA-0001", "Owusu", "Adwoa")
    st2 = make_student("THSA-0002", "Mensah", "Kofi", "M")
    st3 = make_student("THSA-0003", "Boateng", "Esi")
    db.flush()
    db.add(Enrollment(id=uuid7(), school_id=school.id, student_id=st1.id,
                      academic_year_id=year_cur.id, class_stream_id=s_b1a.id,
                      status="ACTIVE", started_on=year_cur.starts_on))
    db.add(Enrollment(id=uuid7(), school_id=school.id, student_id=st2.id,
                      academic_year_id=year_cur.id, class_stream_id=s_b1a.id,
                      status="ACTIVE", started_on=year_cur.starts_on))
    db.add(Enrollment(id=uuid7(), school_id=school.id, student_id=st3.id,
                      academic_year_id=year_cur.id, class_stream_id=s_b2a.id,
                      status="ACTIVE", started_on=year_cur.starts_on))
    db.flush()
    ids.update(st1=st1.id, st2=st2.id, st3=st3.id)

    # ---------------- Phase 4 catalog: competencies, domains, templates, scales, schemes
    curriculum.bootstrap_catalogs(db, school.id)
    reports.ensure_default_templates(db, school.id)

    PRIMARY_BANDS = [
        {"min_score": 80, "max_score": 100, "code": "A", "remark": "Excellent", "rank": 1},
        {"min_score": 70, "max_score": 79.99, "code": "B", "remark": "Very Good", "rank": 2},
        {"min_score": 60, "max_score": 69.99, "code": "C", "remark": "Good", "rank": 3},
        {"min_score": 50, "max_score": 59.99, "code": "D", "remark": "Credit", "rank": 4},
        {"min_score": 40, "max_score": 49.99, "code": "E", "remark": "Pass", "rank": 5},
        {"min_score": 0, "max_score": 39.99, "code": "F", "remark": "Fail", "rank": 6},
    ]
    grading.create_scale(db, school_id=school.id, name="Primary scale (config)",
                         bands_payload=PRIMARY_BANDS, scope_band="PRIMARY", is_default=False)
    grading.create_scale(db, school_id=school.id, name="School default scale",
                         bands_payload=PRIMARY_BANDS, is_default=True)

    # assessment schemes: grade-wide config rows (never hard-coded weights, BR-M01)
    for grade_code in ("B1", "B2"):
        assess_svc.upsert_scheme(
            db, school_id=school.id, academic_year_id=year_cur.id, term_id=term1.id,
            grade_id=grades[grade_code].id, subject_id=None,
            components_payload=[
                {"code": "CLASS_SCORE", "name": "Class Score", "kind": "CLASS",
                 "weight_pct": 50, "max_score": 100},
                {"code": "TERMINAL_EXAM", "name": "Terminal Examination", "kind": "EXAM",
                 "weight_pct": 50, "max_score": 100}])
    assess_svc.upsert_scheme(
        db, school_id=school.id, academic_year_id=year_cur.id, term_id=term1.id,
        grade_id=grades["JHS3"].id, subject_id=None,
        components_payload=[
            {"code": "CLASS_SCORE", "name": "Continuous Assessment", "kind": "CLASS",
             "weight_pct": 30, "max_score": 100},
            {"code": "TERMINAL_EXAM", "name": "Terminal Examination", "kind": "EXAM",
             "weight_pct": 70, "max_score": 100}])
    db.flush()

    # subject ids used across tests
    from app.models.core import Subject  # noqa: E402
    ids["subject_eng"] = db.scalar(
        select(Subject).where(Subject.school_id == school.id, Subject.code == "ENG")).id
    ids["subject_mat"] = db.scalar(
        select(Subject).where(Subject.school_id == school.id, Subject.code == "MAT")).id
    ids["subject_sci"] = db.scalar(
        select(Subject).where(Subject.school_id == school.id, Subject.code == "SCI")).id

    # parent user linked to st1 + st2 (siblings)
    guardian = ParentGuardian(id=uuid7(), school_id=school.id, name="Owusu Guardian",
                              phone="+233241234567")
    db.add(guardian)
    db.flush()
    db.add(ParentStudentRelationship(id=uuid7(), school_id=school.id,
                                     parent_id=guardian.id, student_id=st1.id,
                                     relationship_type="MOTHER", is_primary_contact=True,
                                     is_billing_contact=True))
    db.add(ParentStudentRelationship(id=uuid7(), school_id=school.id,
                                     parent_id=guardian.id, student_id=st2.id,
                                     relationship_type="MOTHER"))
    db.flush()

    # advance the admission-code sequence past the hand-seeded students
    from app.models.core import DocumentSequence
    db.add(DocumentSequence(id=uuid7(), school_id=school.id, key="ADMISSION_CODE",
                            prefix="THSA", current_value=3))
    db.flush()
    ids["parent"] = make_user("parentU", rbac.PARENT, parent_id=guardian.id).id
    ids["guardian"] = guardian.id

    db.commit()
    db.close()
    return ids


@pytest.fixture(scope="session")
def ids() -> dict:
    return _bootstrap()


@pytest.fixture()
def client(ids) -> TestClient:
    """Fresh cookie jar per test (no leaked sessions between tests)."""
    return TestClient(app, base_url="http://testserver")


def login(client: TestClient, username: str, password: str = PASSWORD) -> str:
    """Log in and return the CSRF token (also stored in the client cookie jar)."""
    r = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["csrf_token"]


def auth_headers(csrf: str) -> dict:
    return {"X-CSRF-Token": csrf}
