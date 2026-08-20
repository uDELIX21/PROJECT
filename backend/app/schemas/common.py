"""Serializers: model → JSON-safe dicts (list projections stay lightweight)."""
import uuid

from app.models.core import (AcademicYear, ClassStream, Enrollment, Grade,
                             ParentGuardian, ParentStudentRelationship, Student,
                             Teacher, Term)


def student(s: Student, detail: bool = False) -> dict:
    out = {
        "id": str(s.id), "admission_code": s.admission_code, "surname": s.surname,
        "other_names": s.other_names, "full_name": s.full_name, "gender": s.gender,
        "date_of_birth": str(s.date_of_birth), "status": s.status,
    }
    if detail:
        out.update({"nationality": s.nationality, "religion": s.religion,
                    "admitted_on": str(s.admitted_on) if s.admitted_on else None,
                    "created_at": s.created_at.isoformat() if s.created_at else None})
    return out


def guardian(g: ParentGuardian) -> dict:
    return {"id": str(g.id), "name": g.name, "phone": g.phone, "phone2": g.phone2,
            "email": g.email, "occupation": g.occupation,
            "residential_address": g.residential_address,
            "ghana_digital_address": g.ghana_digital_address,
            "latitude": float(g.latitude) if g.latitude is not None else None,
            "longitude": float(g.longitude) if g.longitude is not None else None,
            "sms_opt_out": g.sms_opt_out}


def relationship(r: ParentStudentRelationship) -> dict:
    return {"id": str(r.id), "parent_id": str(r.parent_id), "student_id": str(r.student_id),
            "relationship_type": r.relationship_type,
            "is_primary_contact": r.is_primary_contact,
            "is_billing_contact": r.is_billing_contact, "source": r.source}


def teacher(t: Teacher) -> dict:
    return {"id": str(t.id), "staff_code": t.staff_code, "full_name": t.full_name,
            "surname": t.surname, "other_names": t.other_names, "gender": t.gender,
            "phone": t.phone, "email": t.email, "job_title": t.job_title,
            "qualification": t.qualification, "employment_status": t.employment_status,
            "hired_on": str(t.hired_on) if t.hired_on else None}


def grade(g: Grade) -> dict:
    return {"id": str(g.id), "code": g.code, "name": g.name, "ordinal": g.ordinal,
            "band": g.band, "department_id": str(g.department_id) if g.department_id else None}


def stream(cs: ClassStream) -> dict:
    return {"id": str(cs.id), "name": cs.name, "section_label": cs.section_label,
            "capacity": cs.capacity, "grade": grade(cs.grade) if cs.grade else None,
            "academic_year_id": str(cs.academic_year_id)}


def year(y: AcademicYear) -> dict:
    return {"id": str(y.id), "name": y.name, "starts_on": str(y.starts_on),
            "ends_on": str(y.ends_on), "status": y.status}


def term(t: Term) -> dict:
    return {"id": str(t.id), "academic_year_id": str(t.academic_year_id), "name": t.name,
            "starts_on": str(t.starts_on), "ends_on": str(t.ends_on), "status": t.status}


def enrollment(e: Enrollment) -> dict:
    return {"id": str(e.id), "student_id": str(e.student_id),
            "academic_year_id": str(e.academic_year_id),
            "class_stream_id": str(e.class_stream_id),
            "stream_name": e.class_stream.name if e.class_stream else None,
            "status": e.status, "is_repeat": e.is_repeat,
            "started_on": str(e.started_on) if e.started_on else None,
            "ended_on": str(e.ended_on) if e.ended_on else None}
