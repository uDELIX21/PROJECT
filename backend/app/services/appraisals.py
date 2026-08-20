"""Teacher appraisal: configurable criteria, evaluator authorization,
confidentiality, acknowledgement (REQ-APR-*, design §03.2.4)."""
import uuid
from datetime import date

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import audit
from app.core.errors import ConflictError, NotFoundError
from app.core.ids import uuid7
from app.models.base import utcnow
from app.models.core import Teacher
from app.models.operations import AppraisalCriterion, AppraisalScore, TeacherAppraisal

SEED_CRITERIA = [
    ("LESSON_PLAN_QUALITY", "Lesson Plan Quality"),
    ("CLASSROOM_MANAGEMENT", "Classroom Management"),
    ("PUNCTUALITY", "Punctuality"),
    ("SYLLABUS_COMPLETION", "Syllabus Completion"),
    ("STUDENT_ENGAGEMENT", "Student Engagement"),
    ("PROFESSIONAL_CONDUCT", "Professional Conduct"),
]


def bootstrap_criteria(db: Session, school_id: uuid.UUID) -> None:
    for code, name in SEED_CRITERIA:
        exists = db.scalar(select(AppraisalCriterion).where(
            AppraisalCriterion.school_id == school_id, AppraisalCriterion.code == code))
        if exists is None:
            db.add(AppraisalCriterion(id=uuid7(), school_id=school_id, code=code,
                                      name=name, max_score=10,
                                      weight_pct=round(100 / len(SEED_CRITERIA), 2)))
    db.flush()


def criteria_for(db: Session, school_id: uuid.UUID) -> list[AppraisalCriterion]:
    return list(db.scalars(select(AppraisalCriterion).where(
        AppraisalCriterion.school_id == school_id,
        AppraisalCriterion.is_active.is_(True))).all())


def create_appraisal(db: Session, *, school_id: uuid.UUID, teacher_id: uuid.UUID,
                     evaluator_user_id: uuid.UUID, period_from: date, period_to: date,
                     request: Request | None = None) -> TeacherAppraisal:
    teacher = db.get(Teacher, teacher_id)
    if teacher is None or teacher.school_id != school_id:
        raise NotFoundError("Teacher not found.")
    overlap = db.scalar(select(TeacherAppraisal).where(
        TeacherAppraisal.teacher_id == teacher_id,
        TeacherAppraisal.period_from <= period_to,
        TeacherAppraisal.period_to >= period_from,
        TeacherAppraisal.status != "DRAFT").limit(1))
    if overlap is not None:
        raise ConflictError("Teacher already has an appraisal for that period.",
                            code="APPRAISAL_OVERLAP")
    row = TeacherAppraisal(id=uuid7(), school_id=school_id, teacher_id=teacher_id,
                           evaluator_user_id=evaluator_user_id,
                           period_from=period_from, period_to=period_to,
                           created_by=evaluator_user_id)
    db.add(row)
    audit(db, actor_id=evaluator_user_id, action="appraisal.created",
          entity_type="teacher_appraisal", entity_id=row.id,
          new={"teacher_id": str(teacher_id)}, request=request)
    db.flush()
    return row


def save_scores(db: Session, appraisal: TeacherAppraisal, scores: list[dict], *,
                actor_id: uuid.UUID, request: Request | None = None) -> None:
    if appraisal.status != "DRAFT":
        raise ConflictError("Appraisal is no longer editable.", code="APPRAISAL_LOCKED")
    criteria = {c.id: c for c in db.scalars(select(AppraisalCriterion).where(
        AppraisalCriterion.school_id == appraisal.school_id)).all()}
    for s in scores:
        criterion = criteria.get(s["criterion_id"])
        if criterion is None:
            raise NotFoundError("Criterion not found.")
        if s["score"] < 0 or s["score"] > criterion.max_score:
            raise ConflictError(
                f"Score for {criterion.name} must be within [0, {criterion.max_score}].",
                code="SCORE_OUT_OF_RANGE")
        row = db.scalar(select(AppraisalScore).where(
            AppraisalScore.appraisal_id == appraisal.id,
            AppraisalScore.criterion_id == s["criterion_id"]))
        if row is None:
            row = AppraisalScore(id=uuid7(), school_id=appraisal.school_id,
                                 appraisal_id=appraisal.id,
                                 criterion_id=s["criterion_id"], score=s["score"],
                                 comment=s.get("comment"))
            db.add(row)
        else:
            row.score = s["score"]
            row.comment = s.get("comment")
    db.flush()


def submit_appraisal(db: Session, appraisal: TeacherAppraisal, *, actor_id: uuid.UUID,
                     overall_comment: str | None = None,
                     request: Request | None = None) -> TeacherAppraisal:
    if appraisal.status != "DRAFT":
        raise ConflictError("Only draft appraisals can be submitted.", code="NOT_DRAFT")
    scores = db.scalars(select(AppraisalScore).where(
        AppraisalScore.appraisal_id == appraisal.id)).all()
    if not scores:
        raise ConflictError("Enter criterion scores before submitting.", code="NO_SCORES")
    criteria = {c.id: c for c in db.scalars(select(AppraisalCriterion).where(
        AppraisalCriterion.school_id == appraisal.school_id)).all()}
    total_weight = sum(float(criteria[s.criterion_id].weight_pct) for s in scores
                       if s.criterion_id in criteria)
    if total_weight > 0:
        weighted = sum(float(s.score) / criteria[s.criterion_id].max_score
                       * float(criteria[s.criterion_id].weight_pct)
                       for s in scores if s.criterion_id in criteria)
        appraisal.overall_rating = round(weighted / total_weight * 10, 2)
    appraisal.overall_comment = overall_comment
    appraisal.status = "SUBMITTED"
    appraisal.submitted_at = utcnow()
    audit(db, actor_id=actor_id, action="appraisal.submitted",
          entity_type="teacher_appraisal", entity_id=appraisal.id,
          new={"rating": appraisal.overall_rating}, request=request)
    # notify the teacher's login (if any)
    from app.models.auth import User
    from app.services import comms
    teacher_user = db.scalar(select(User).where(
        User.teacher_id == appraisal.teacher_id, User.status == "ACTIVE"))
    if teacher_user:
        comms.notify_user(db, school_id=appraisal.school_id, user_id=teacher_user.id,
                          kind="APPRAISAL_SUBMITTED", title="Appraisal submitted",
                          body="Your appraisal has been submitted for acknowledgement.")
    db.flush()
    return appraisal


def acknowledge_appraisal(db: Session, appraisal: TeacherAppraisal, *, actor_id: uuid.UUID,
                          request: Request | None = None) -> TeacherAppraisal:
    """Teacher acknowledgement step (design §27)."""
    if appraisal.status != "SUBMITTED":
        raise ConflictError("Nothing to acknowledge.", code="NOT_SUBMITTED")
    appraisal.status = "ACKNOWLEDGED"
    appraisal.acknowledged_at = utcnow()
    audit(db, actor_id=actor_id, action="appraisal.acknowledged",
          entity_type="teacher_appraisal", entity_id=appraisal.id, request=request)
    db.flush()
    return appraisal
