"""Bootstrap catalog data: permissions, roles+matrix, grades, departments, subjects.

Used by the seed script and test fixtures; idempotent.
"""
import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import rbac
from app.core.ids import uuid7
from app.models.auth import Permission, Role, RolePermission
from app.models.core import (Department, Grade, GradeSubject, School, SchoolSetting,
                             Subject)

GRADES: list[tuple[str, str, int, str, str]] = [
    # code, name, ordinal, band, department_code
    ("CRECHE", "Crèche", 1, "EARLY_CHILDHOOD", "EC"),
    ("NUR1", "Nursery 1", 2, "EARLY_CHILDHOOD", "EC"),
    ("NUR2", "Nursery 2", 3, "EARLY_CHILDHOOD", "EC"),
    ("KG1", "KG 1", 4, "EARLY_CHILDHOOD", "EC"),
    ("KG2", "KG 2", 5, "EARLY_CHILDHOOD", "EC"),
    ("B1", "Basic 1", 6, "PRIMARY", "PRI"),
    ("B2", "Basic 2", 7, "PRIMARY", "PRI"),
    ("B3", "Basic 3", 8, "PRIMARY", "PRI"),
    ("B4", "Basic 4", 9, "PRIMARY", "PRI"),
    ("B5", "Basic 5", 10, "PRIMARY", "PRI"),
    ("B6", "Basic 6", 11, "PRIMARY", "PRI"),
    ("JHS1", "JHS 1", 12, "JHS", "JHS"),
    ("JHS2", "JHS 2", 13, "JHS", "JHS"),
    ("JHS3", "JHS 3", 14, "JHS", "JHS"),
]

PRIMARY_SUBJECTS = [
    ("ENG", "English Language"), ("MAT", "Mathematics"), ("SCI", "Integrated Science"),
    ("OWOP", "Our World Our People"), ("RME", "Religious & Moral Education"),
    ("CREATIVE", "Creative Arts"), ("FRENCH", "French"), ("COMPUTING", "Computing"),
    ("PE", "Physical Education"),
]
JHS_SUBJECTS = [
    ("ENG", "English Language"), ("MAT", "Mathematics"), ("SCI", "Integrated Science"),
    ("SOCIAL", "Social Studies"), ("RME", "Religious & Moral Education"),
    ("CREATIVE", "Creative Arts & Design"), ("FRENCH", "French"), ("COMPUTING", "Computing"),
    ("CAREER", "Career Technology"), ("PE", "Physical Education"),
]
EC_SUBJECTS = [
    ("NUMERACY", "Numeracy"), ("LITERACY", "Literacy"), ("CREATIVE", "Creative Activities"),
]


def bootstrap_permissions(db: Session) -> None:
    existing = {p.code for p in db.scalars(select(Permission)).all()}
    for code, (name, desc) in rbac.PERMISSIONS.items():
        if code not in existing:
            db.add(Permission(code=code, name=name, description=desc))
    db.flush()


def bootstrap_roles(db: Session, school_id: uuid.UUID) -> dict[str, Role]:
    existing = {r.code: r for r in db.scalars(
        select(Role).where(Role.school_id == school_id)).all()}
    roles: dict[str, Role] = {}
    for code, name in rbac.ROLE_NAMES.items():
        role = existing.get(code)
        if role is None:
            role = Role(id=uuid7(), school_id=school_id, code=code, name=name, is_system=True)
            db.add(role)
            db.flush()
        roles[code] = role
        have = {rp.permission_code for rp in db.scalars(
            select(RolePermission).where(RolePermission.role_id == role.id)).all()}
        for perm in rbac.ROLE_MATRIX[code]:
            if perm not in have:
                db.add(RolePermission(role_id=role.id, permission_code=perm))
    db.flush()
    return roles


def bootstrap_departments(db: Session, school_id: uuid.UUID) -> dict[str, Department]:
    codes = {"EC": "Early Childhood", "PRI": "Primary", "JHS": "Junior High School"}
    out: dict[str, Department] = {}
    for code, name in codes.items():
        dept = db.scalar(select(Department).where(Department.school_id == school_id,
                                                  Department.code == code))
        if dept is None:
            dept = Department(id=uuid7(), school_id=school_id, code=code, name=name)
            db.add(dept)
            db.flush()
        out[code] = dept
    return out


def bootstrap_grades(db: Session, school_id: uuid.UUID,
                     departments: dict[str, Department]) -> dict[str, Grade]:
    out: dict[str, Grade] = {}
    for code, name, ordinal, band, dept_code in GRADES:
        grade = db.scalar(select(Grade).where(Grade.school_id == school_id,
                                              Grade.code == code))
        if grade is None:
            grade = Grade(id=uuid7(), school_id=school_id, code=code, name=name,
                          ordinal=ordinal, band=band,
                          department_id=departments[dept_code].id)
            db.add(grade)
            db.flush()
        out[code] = grade
    return out


def bootstrap_subjects(db: Session, school_id: uuid.UUID,
                       grades: dict[str, Grade]) -> dict[str, Subject]:
    out: dict[str, Subject] = {}
    for code, name in EC_SUBJECTS + PRIMARY_SUBJECTS + JHS_SUBJECTS:
        subj = db.scalar(select(Subject).where(Subject.school_id == school_id,
                                               Subject.code == code))
        if subj is None:
            subj = Subject(id=uuid7(), school_id=school_id, code=code, name=name)
            db.add(subj)
            db.flush()
        out[code] = subj

    def link(grade_codes: list[str], subject_codes: list[str]) -> None:
        for gc in grade_codes:
            for sc in subject_codes:
                exists = db.scalar(select(GradeSubject).where(
                    GradeSubject.grade_id == grades[gc].id,
                    GradeSubject.subject_id == out[sc].id))
                if exists is None:
                    db.add(GradeSubject(grade_id=grades[gc].id, subject_id=out[sc].id))

    link([g[0] for g in GRADES if g[3] == "EARLY_CHILDHOOD"], [s[0] for s in EC_SUBJECTS])
    link([g[0] for g in GRADES if g[3] == "PRIMARY"], [s[0] for s in PRIMARY_SUBJECTS])
    link([g[0] for g in GRADES if g[3] == "JHS"], [s[0] for s in JHS_SUBJECTS])
    db.flush()
    return out


def ensure_setting(db: Session, school_id: uuid.UUID, key: str, value, description: str = "") -> None:
    row = db.scalar(select(SchoolSetting).where(SchoolSetting.school_id == school_id,
                                                SchoolSetting.key == key))
    if row is None:
        db.add(SchoolSetting(id=uuid7(), school_id=school_id, key=key,
                             value=value, description=description))


def create_school(db: Session, name: str, admission_code_prefix: str | None = None,
                  **fields) -> School:
    school = School(id=uuid7(), name=name, **fields)
    db.add(school)
    db.flush()
    from app.core.config import get_settings
    ensure_setting(db, school.id, "admission_code_prefix",
                   admission_code_prefix or get_settings().admission_code_prefix,
                   "Prefix for generated admission codes")
    ensure_setting(db, school.id, "demo_data", True,
                   "True when all records are synthetic demo data")
    ensure_setting(db, school.id, "report_positions_enabled", True,
                   "Show class position/rank on report cards (decision D2)")
    ensure_setting(db, school.id, "student_accounts_enabled", False,
                   "Whether student login accounts are provisioned (decision D7)")
    return school
