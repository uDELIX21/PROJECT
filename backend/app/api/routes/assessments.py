"""Assessment endpoints: schemes, mark sheets, locking, corrections, results (design §07)."""
import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import rbac
from app.api.deps import AuthContext, get_school, require
from app.core.db import get_db
from app.core.errors import ForbiddenError, NotFoundError
from app.models.academic import Assessment, AssessmentScore, ScoreOverride
from app.models.core import ClassStream, Grade, Subject, Term
from app.schemas.requests import (CorrectionRequestIn, CorrectionResolveIn,
                                  SchemeUpsertIn, ScoresSaveIn, SheetRefIn)
from app.services import assessment as svc

router = APIRouter(prefix="/assessments", tags=["assessments"])


def _stream(db: Session, school_id: uuid.UUID, stream_id: uuid.UUID) -> ClassStream:
    s = db.get(ClassStream, stream_id)
    if s is None or s.school_id != school_id:
        raise NotFoundError("Class stream not found.")
    return s


def _assert_teacher_scope(ctx: AuthContext, db: Session, stream: ClassStream,
                           subject_id: uuid.UUID | None = None) -> None:
    """Teachers may only write marks for assigned classes/subjects (REQ-MRK-01)."""
    if ctx.user.teacher_id is None:
        return
    from app.models.core import TeacherAssignment
    stmt = select(TeacherAssignment).where(
        TeacherAssignment.teacher_id == ctx.user.teacher_id,
        TeacherAssignment.class_stream_id == stream.id,
        TeacherAssignment.is_active.is_(True))
    assignments = db.scalars(stmt).all()
    if not assignments:
        raise ForbiddenError("You are not assigned to this class.", code="NOT_ASSIGNED_CLASS")
    if subject_id is not None:
        covers = any(a.subject_id == subject_id or a.role == "FORM_TEACHER" for a in assignments)
        if not covers:
            raise ForbiddenError("You are not assigned to this subject in this class.",
                                 code="NOT_ASSIGNED_SUBJECT")


# --------------------------------------------------------------------------- schemes

@router.get("/schemes")
def list_schemes(term_id: uuid.UUID, grade_id: uuid.UUID,
                 subject_id: uuid.UUID | None = None,
                 ctx: AuthContext = Depends(require(rbac.VIEW_GRADES_CONFIG)),
                 db: Session = Depends(get_db)):
    school = get_school(db)
    scheme = svc.resolve_scheme(db, school_id=school.id, term_id=term_id,
                                grade_id=grade_id, subject_id=subject_id)
    if scheme is None:
        return {"scheme": None, "components": []}
    comps = svc.scheme_components(db, scheme.id)
    return {"scheme": {"id": str(scheme.id), "name": scheme.name,
                       "grade_id": str(scheme.grade_id),
                       "subject_id": str(scheme.subject_id) if scheme.subject_id else None},
            "components": [{"id": str(c.id), "code": c.code, "name": c.name, "kind": c.kind,
                            "weight_pct": float(c.weight_pct), "max_score": float(c.max_score),
                            "aggregation": c.aggregation} for c in comps]}


@router.put("/schemes")
def upsert_scheme(body: SchemeUpsertIn, request: Request,
                  ctx: AuthContext = Depends(require(rbac.MANAGE_GRADES_CONFIG)),
                  db: Session = Depends(get_db)):
    school = get_school(db)
    grade = db.get(Grade, body.grade_id)
    if grade is None or grade.school_id != school.id:
        raise NotFoundError("Grade not found.")
    svc.assert_not_ecd_band(db, grade)  # BR-M07
    scheme = svc.upsert_scheme(
        db, school_id=school.id, academic_year_id=body.academic_year_id,
        term_id=body.term_id, grade_id=body.grade_id, subject_id=body.subject_id,
        components_payload=[c.model_dump() for c in body.components],
        name=body.name, actor_id=ctx.user.id, request=request)
    db.commit()
    return {"id": str(scheme.id),
            "components": [c.model_dump() for c in body.components]}


# --------------------------------------------------------------------------- mark sheets

def _sheet_or_404(db: Session, school_id: uuid.UUID, sheet_id: uuid.UUID) -> Assessment:
    sheet = db.get(Assessment, sheet_id)
    if sheet is None or sheet.school_id != school_id:
        raise NotFoundError("Mark sheet not found.")
    return sheet


@router.get("/sheets")
def get_sheet(term_id: uuid.UUID, class_stream_id: uuid.UUID, subject_id: uuid.UUID,
              component_id: uuid.UUID | None = None,
              ctx: AuthContext = Depends(require(rbac.VIEW_STUDENT)),
              db: Session = Depends(get_db)):
    """Sheet + current scores (draft view for teachers; results view uses /results)."""
    school = get_school(db)
    stream = _stream(db, school.id, class_stream_id)
    _assert_teacher_scope(ctx, db, stream, subject_id)
    term = db.get(Term, term_id)
    if term is None or term.school_id != school.id:
        raise NotFoundError("Term not found.")
    if component_id is None:
        grade = db.get(Grade, stream.grade_id)
        scheme = svc.resolve_scheme(db, school_id=school.id, term_id=term_id,
                                    grade_id=grade.id, subject_id=subject_id)
        if scheme is None:
            return {"sheet": None, "components": [], "scores": []}
        comps = svc.scheme_components(db, scheme.id)
        return {"sheet": None,
                "components": [{"id": str(c.id), "code": c.code, "name": c.name,
                                "max_score": float(c.max_score),
                                "weight_pct": float(c.weight_pct)} for c in comps],
                "scores": []}
    sheet = svc.get_or_create_sheet(db, school_id=school.id, term_id=term_id,
                                    class_stream_id=class_stream_id,
                                    subject_id=subject_id, component_id=component_id)
    scores = db.scalars(select(AssessmentScore).where(
        AssessmentScore.assessment_id == sheet.id)).all()
    db.commit()  # get_or_create may have inserted the sheet
    return {"sheet": {"id": str(sheet.id), "status": sheet.status,
                      "title": sheet.title, "version": sheet.version,
                      "component_id": str(sheet.component_id)},
            "components": [{"id": str(sheet.component.id), "code": sheet.component.code,
                            "name": sheet.component.name,
                            "max_score": float(sheet.component.max_score)}],
            "scores": [{"id": str(s.id), "enrollment_id": str(s.enrollment_id),
                        "raw_score": float(s.raw_score) if s.raw_score is not None else None,
                        "is_absent": s.is_absent, "note": s.note} for s in scores]}


@router.post("/sheets/scores")
def save_scores(body: ScoresSaveIn, request: Request,
                ctx: AuthContext = Depends(require(rbac.ENTER_MARKS)),
                db: Session = Depends(get_db)):
    school = get_school(db)
    sheet = _sheet_or_404(db, school.id, body.sheet_id)
    stream = _stream(db, school.id, sheet.class_stream_id)
    _assert_teacher_scope(ctx, db, stream, sheet.subject_id)
    term = db.get(Term, sheet.term_id)
    svc.assert_term_open(term)  # BR-A03
    n = svc.save_draft_scores(db, sheet,
                              [e.model_dump() for e in body.entries],
                              actor_id=ctx.user.id, request=request)
    db.commit()
    return {"saved": n, "sheet_version": sheet.version, "status": sheet.status}


@router.post("/sheets/submit")
def submit_sheet(body: SheetRefIn, request: Request,
                 ctx: AuthContext = Depends(require(rbac.SUBMIT_MARKS)),
                 db: Session = Depends(get_db)):
    school = get_school(db)
    sheet = _sheet_or_404(db, school.id, body.sheet_id)
    stream = _stream(db, school.id, sheet.class_stream_id)
    _assert_teacher_scope(ctx, db, stream, sheet.subject_id)
    svc.submit_sheet(db, sheet, actor_id=ctx.user.id,
                     allow_incomplete=body.allow_incomplete, request=request)
    db.commit()
    return {"status": sheet.status, "submitted_at": sheet.submitted_at.isoformat()
            if sheet.submitted_at else None}


@router.post("/sheets/lock")
def lock_sheet(body: SheetRefIn, request: Request,
               ctx: AuthContext = Depends(require(rbac.OVERRIDE_MARKS)),
               db: Session = Depends(get_db)):
    school = get_school(db)
    sheet = _sheet_or_404(db, school.id, body.sheet_id)
    svc.lock_sheet(db, sheet, actor_id=ctx.user.id, request=request)
    db.commit()
    return {"status": sheet.status}


# --------------------------------------------------------------------------- corrections

@router.post("/corrections", status_code=201)
def request_correction(body: CorrectionRequestIn, request: Request,
                       ctx: AuthContext = Depends(require(rbac.ENTER_MARKS)),
                       db: Session = Depends(get_db)):
    school = get_school(db)
    ov = svc.request_correction(db, school_id=school.id,
                                assessment_score_id=body.assessment_score_id,
                                new_score=body.new_score, reason=body.reason,
                                requester_id=ctx.user.id, request=request)
    db.commit()
    return {"id": str(ov.id), "status": ov.status}


@router.get("/corrections")
def list_corrections(status: str = "PENDING",
                     ctx: AuthContext = Depends(require(rbac.OVERRIDE_MARKS)),
                     db: Session = Depends(get_db)):
    school = get_school(db)
    rows = db.scalars(select(ScoreOverride).where(
        ScoreOverride.school_id == school.id, ScoreOverride.status == status)
        .order_by(ScoreOverride.created_at.desc()).limit(100)).all()
    return {"items": [{"id": str(r.id), "assessment_score_id": str(r.assessment_score_id),
                       "original_score": float(r.original_score)
                       if r.original_score is not None else None,
                       "new_score": float(r.new_score) if r.new_score is not None else None,
                       "reason": r.reason, "status": r.status,
                       "requested_by": str(r.requested_by)} for r in rows]}


@router.post("/corrections/{override_id}/resolve")
def resolve_correction(override_id: uuid.UUID, body: CorrectionResolveIn, request: Request,
                       ctx: AuthContext = Depends(require(rbac.OVERRIDE_MARKS)),
                       db: Session = Depends(get_db)):
    school = get_school(db)
    ov = db.get(ScoreOverride, override_id)
    if ov is None or ov.school_id != school.id:
        raise NotFoundError("Correction request not found.")
    svc.resolve_correction(db, ov, approve=body.approve, approver_id=ctx.user.id,
                           request=request)
    db.commit()
    return {"status": ov.status}


# --------------------------------------------------------------------------- results

@router.get("/results")
def results(term_id: uuid.UUID, class_stream_id: uuid.UUID, subject_id: uuid.UUID,
            ctx: AuthContext = Depends(require(rbac.VIEW_REPORT)),
            db: Session = Depends(get_db)):
    school = get_school(db)
    stream = _stream(db, school.id, class_stream_id)
    grade = db.get(Grade, stream.grade_id)
    svc.assert_not_ecd_band(db, grade)
    term = db.get(Term, term_id)
    if term is None or term.school_id != school.id:
        raise NotFoundError("Term not found.")
    res = svc.compute_stream_subject_results(
        db, school_id=school.id, term_id=term_id, class_stream_id=class_stream_id,
        subject_id=subject_id, grade=grade, academic_year_id=term.academic_year_id)
    return res
