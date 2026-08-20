"""Assessment engine: configurable schemes, mark sheets, locking, corrections (BR-M)."""
import uuid
from datetime import datetime, timezone

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import audit
from app.core.errors import ConflictError, LockedError, NotFoundError
from app.core.ids import uuid7
from app.models.academic import (Assessment, AssessmentComponent, AssessmentScheme,
                                 AssessmentScore, ScoreOverride)
from app.models.base import utcnow
from app.models.core import ClassStream, Enrollment, Grade, Student, Term
from app.services import grading, scoring

MAX_DECISIONS = 100


# --------------------------------------------------------------------------- schemes

def resolve_scheme(db: Session, *, school_id: uuid.UUID, term_id: uuid.UUID,
                   grade_id: uuid.UUID, subject_id: uuid.UUID | None) -> AssessmentScheme | None:
    """Most specific scheme wins: subject-scoped → grade-wide."""
    if subject_id is not None:
        s = db.scalar(select(AssessmentScheme).where(
            AssessmentScheme.school_id == school_id,
            AssessmentScheme.term_id == term_id,
            AssessmentScheme.grade_id == grade_id,
            AssessmentScheme.subject_id == subject_id))
        if s is not None:
            return s
    return db.scalar(select(AssessmentScheme).where(
        AssessmentScheme.school_id == school_id,
        AssessmentScheme.term_id == term_id,
        AssessmentScheme.grade_id == grade_id,
        AssessmentScheme.subject_id.is_(None)))


def scheme_components(db: Session, scheme_id: uuid.UUID) -> list[AssessmentComponent]:
    return list(db.scalars(select(AssessmentComponent)
                           .where(AssessmentComponent.scheme_id == scheme_id)
                           .order_by(AssessmentComponent.ordinal)).all())


def upsert_scheme(db: Session, *, school_id: uuid.UUID, academic_year_id: uuid.UUID,
                  term_id: uuid.UUID, grade_id: uuid.UUID,
                  subject_id: uuid.UUID | None, components_payload: list[dict],
                  name: str = "Standard scheme", actor_id: uuid.UUID | None = None,
                  request: Request | None = None) -> AssessmentScheme:
    """Create or replace a scheme's components. Weights must sum to 100 (BR-M01)."""
    if not components_payload:
        raise ConflictError("At least one component is required.", code="NO_COMPONENTS")
    total = sum(float(c["weight_pct"]) for c in components_payload)
    if abs(total - 100.0) > 1e-6:
        raise ConflictError(f"Component weights must sum to exactly 100 (got {total}).",
                            code="WEIGHTS_SUM_INVALID")
    codes = [c["code"] for c in components_payload]
    if len(set(codes)) != len(codes):
        raise ConflictError("Component codes must be unique within a scheme.",
                            code="COMPONENT_CODE_DUPLICATE")

    scheme = db.scalar(select(AssessmentScheme).where(
        AssessmentScheme.school_id == school_id,
        AssessmentScheme.academic_year_id == academic_year_id,
        AssessmentScheme.term_id == term_id,
        AssessmentScheme.grade_id == grade_id,
        AssessmentScheme.subject_id == subject_id if subject_id is not None
        else AssessmentScheme.subject_id.is_(None)))
    created = scheme is None
    if created:
        scheme = AssessmentScheme(id=uuid7(), school_id=school_id,
                                  academic_year_id=academic_year_id, term_id=term_id,
                                  grade_id=grade_id, subject_id=subject_id, name=name,
                                  created_by=actor_id)
        db.add(scheme)
        db.flush()
    else:
        # replacing components is blocked once sheets exist for this scheme (history safety)
        existing_sheets = db.scalar(select(Assessment.id).where(
            AssessmentComponent.scheme_id == scheme.id,
            Assessment.component_id == AssessmentComponent.id).limit(1))
        if existing_sheets is not None:
            raise ConflictError(
                "Scheme already has mark sheets; create a new scheme instead of editing.",
                code="SCHEME_IN_USE")
        for old in scheme_components(db, scheme.id):
            db.delete(old)
    for idx, c in enumerate(components_payload):
        db.add(AssessmentComponent(
            id=uuid7(), school_id=school_id, scheme_id=scheme.id, code=c["code"],
            name=c.get("name") or c["code"], kind=c.get("kind", "CLASS"),
            weight_pct=float(c["weight_pct"]), max_score=float(c.get("max_score", 100)),
            aggregation=c.get("aggregation", "DIRECT"), ordinal=idx + 1))
    audit(db, actor_id=actor_id, action="scheme.upserted", entity_type="assessment_scheme",
          entity_id=scheme.id, new={"components": components_payload}, request=request)
    db.flush()
    return scheme


# --------------------------------------------------------------------------- sheets

def get_term(db: Session, school_id: uuid.UUID, term_id: uuid.UUID) -> Term:
    t = db.get(Term, term_id)
    if t is None or t.school_id != school_id:
        raise NotFoundError("Term not found.")
    return t


def assert_term_open(term: Term) -> None:
    if term.status != "ACTIVE":
        raise LockedError(f"Term '{term.name}' is {term.status.lower()}; "
                          "marks entry requires the active term (BR-A03).",
                          code="TERM_CLOSED")


def assert_not_ecd_band(db: Session, grade: Grade) -> None:
    """Early childhood is qualitative — numeric schemes forbidden (BR-M07)."""
    if grade.band == "EARLY_CHILDHOOD":
        raise ConflictError(
            "Early childhood classes use developmental assessment, not numeric marks (BR-M07).",
            code="ECD_NUMERIC_NOT_ALLOWED")


def get_or_create_sheet(db: Session, *, school_id: uuid.UUID, term_id: uuid.UUID,
                        class_stream_id: uuid.UUID, subject_id: uuid.UUID,
                        component_id: uuid.UUID) -> Assessment:
    component = db.get(AssessmentComponent, component_id)
    if component is None or component.school_id != school_id:
        raise NotFoundError("Assessment component not found.")
    sheet = db.scalar(select(Assessment).where(
        Assessment.term_id == term_id,
        Assessment.class_stream_id == class_stream_id,
        Assessment.subject_id == subject_id,
        Assessment.component_id == component_id))
    if sheet is None:
        stream = db.get(ClassStream, class_stream_id)
        sheet = Assessment(id=uuid7(), school_id=school_id, term_id=term_id,
                           class_stream_id=class_stream_id, subject_id=subject_id,
                           component_id=component_id,
                           title=f"{component.name}")
        db.add(sheet)
        db.flush()
    return sheet


def save_draft_scores(db: Session, sheet: Assessment, entries: list[dict], *,
                      actor_id: uuid.UUID | None, request: Request | None = None) -> int:
    """Draft-only writes (BR-M03). Validates score ranges (BR-M06)."""
    if sheet.status != "DRAFT":
        raise LockedError(
            f"Sheet is {sheet.status}; use the correction workflow for changes (BR-M04).",
            code="MARKS_LOCKED")
    component = sheet.component
    count = 0
    for e in entries:
        raw = e.get("raw_score")
        if raw is not None:
            raw = float(raw)
            if raw < 0 or raw > float(component.max_score):
                raise ConflictError(
                    f"Score {raw} out of range [0, {component.max_score}] (BR-M06).",
                    code="SCORE_OUT_OF_RANGE")
        score = db.scalar(select(AssessmentScore).where(
            AssessmentScore.assessment_id == sheet.id,
            AssessmentScore.enrollment_id == e["enrollment_id"]))
        if score is None:
            score = AssessmentScore(id=uuid7(), school_id=sheet.school_id,
                                    assessment_id=sheet.id,
                                    enrollment_id=e["enrollment_id"],
                                    raw_score=raw, is_absent=bool(e.get("is_absent", False)),
                                    note=e.get("note"))
            db.add(score)
        else:
            score.raw_score = raw
            score.is_absent = bool(e.get("is_absent", False))
            score.note = e.get("note")
            score.version += 1
        count += 1
    sheet.version += 1
    sheet.updated_by = actor_id
    db.flush()
    return count


def submit_sheet(db: Session, sheet: Assessment, *, actor_id: uuid.UUID,
                 allow_incomplete: bool = False, request: Request | None = None) -> Assessment:
    if sheet.status != "DRAFT":
        raise ConflictError("Only draft sheets can be submitted.", code="NOT_DRAFT")
    roster = db.scalars(select(Enrollment).where(
        Enrollment.class_stream_id == sheet.class_stream_id,
        Enrollment.academic_year_id == db.get(Term, sheet.term_id).academic_year_id,
        Enrollment.status == "ACTIVE")).all()
    entered = {s.enrollment_id for s in db.scalars(select(AssessmentScore).where(
        AssessmentScore.assessment_id == sheet.id)).all()}
    missing = [e for e in roster if e.id not in entered]
    if missing and not allow_incomplete:
        raise ConflictError(
            f"{len(missing)} student(s) have no score. Enter all scores or pass "
            "allow_incomplete=true to submit anyway.", code="SHEET_INCOMPLETE")
    sheet.status = "SUBMITTED"
    sheet.submitted_by = actor_id
    sheet.submitted_at = utcnow()
    sheet.version += 1
    audit(db, actor_id=actor_id, action="sheet.submitted", entity_type="assessment",
          entity_id=sheet.id, new={"missing": len(missing)}, request=request)
    db.flush()
    return sheet


def lock_sheet(db: Session, sheet: Assessment, *, actor_id: uuid.UUID,
               request: Request | None = None) -> Assessment:
    if sheet.status != "SUBMITTED":
        raise ConflictError("Only submitted sheets can be locked.", code="NOT_SUBMITTED")
    sheet.status = "LOCKED"
    sheet.locked_by = actor_id
    sheet.locked_at = utcnow()
    sheet.version += 1
    audit(db, actor_id=actor_id, action="sheet.locked", entity_type="assessment",
          entity_id=sheet.id, request=request)
    db.flush()
    return sheet


# --------------------------------------------------------------------------- corrections

def request_correction(db: Session, *, school_id: uuid.UUID, assessment_score_id: uuid.UUID,
                       new_score: float | None, reason: str, requester_id: uuid.UUID,
                       request: Request | None = None) -> ScoreOverride:
    score = db.get(AssessmentScore, assessment_score_id)
    if score is None or score.school_id != school_id:
        raise NotFoundError("Score not found.")
    sheet = db.get(Assessment, score.assessment_id)
    if sheet.status == "DRAFT":
        raise ConflictError("Sheet is still a draft — edit it directly.", code="SHEET_DRAFT")
    if new_score is not None:
        comp = sheet.component
        if new_score < 0 or new_score > float(comp.max_score):
            raise ConflictError("Proposed score out of range.", code="SCORE_OUT_OF_RANGE")
    pending = db.scalar(select(ScoreOverride).where(
        ScoreOverride.assessment_score_id == assessment_score_id,
        ScoreOverride.status == "PENDING"))
    if pending is not None:
        raise ConflictError("A correction request is already pending for this score.",
                            code="CORRECTION_PENDING")
    ov = ScoreOverride(id=uuid7(), school_id=school_id,
                       assessment_score_id=assessment_score_id,
                       original_score=score.raw_score, new_score=new_score,
                       reason=reason, requested_by=requester_id, status="PENDING")
    db.add(ov)
    audit(db, actor_id=requester_id, action="correction.requested",
          entity_type="score_override", entity_id=ov.id,
          previous={"raw_score": float(score.raw_score) if score.raw_score is not None else None},
          new={"proposed": new_score}, reason=reason, request=request)
    db.flush()
    return ov


def resolve_correction(db: Session, override: ScoreOverride, *, approve: bool,
                       approver_id: uuid.UUID, request: Request | None = None) -> ScoreOverride:
    if override.status != "PENDING":
        raise ConflictError("Correction request already resolved.", code="CORRECTION_RESOLVED")
    score = db.get(AssessmentScore, override.assessment_score_id)
    if approve:
        original = score.raw_score
        score.raw_score = override.new_score
        score.version += 1
        override.status = "APPROVED"
        override.approved_by = approver_id
        override.approved_at = utcnow()
        sheet = db.get(Assessment, score.assessment_id)
        sheet.version += 1
        # full trail: original + new + reason + approver + actor + timestamp (BR-M04)
        audit(db, actor_id=approver_id, action="correction.approved",
              entity_type="assessment_score", entity_id=score.id,
              previous={"raw_score": float(original) if original is not None else None},
              new={"raw_score": float(override.new_score) if override.new_score is not None else None,
                   "requested_by": str(override.requested_by)},
              reason=override.reason, request=request)
    else:
        override.status = "REJECTED"
        override.approved_by = approver_id
        override.approved_at = utcnow()
        audit(db, actor_id=approver_id, action="correction.rejected",
              entity_type="score_override", entity_id=override.id,
              reason=override.reason, request=request)
    db.flush()
    return override


# --------------------------------------------------------------------------- results

def compute_stream_subject_results(db: Session, *, school_id: uuid.UUID, term_id: uuid.UUID,
                                   class_stream_id: uuid.UUID, subject_id: uuid.UUID,
                                   grade: Grade, academic_year_id: uuid.UUID,
                                   round_decimals: int = 1) -> dict:
    """Deterministic results table for one class×subject (spec §8 pipeline)."""
    scheme = resolve_scheme(db, school_id=school_id, term_id=term_id,
                            grade_id=grade.id, subject_id=subject_id)
    if scheme is None:
        raise ConflictError(
            "No assessment scheme configured for this grade/term/subject.",
            code="NO_SCHEME")
    components = scheme_components(db, scheme.id)
    specs = [scoring.ComponentSpec(code=c.code, weight_pct=float(c.weight_pct),
                                   max_score=float(c.max_score), aggregation=c.aggregation)
             for c in components]
    sheets = db.scalars(select(Assessment).where(
        Assessment.term_id == term_id,
        Assessment.class_stream_id == class_stream_id,
        Assessment.subject_id == subject_id,
        Assessment.component_id.in_([c.id for c in components]))).all()
    sheet_by_component = {s.component_id: s for s in sheets}

    enrollments = db.execute(select(Enrollment, Student).join(
        Student, Enrollment.student_id == Student.id).where(
        Enrollment.class_stream_id == class_stream_id,
        Enrollment.academic_year_id == academic_year_id,
        Enrollment.status.in_(("ACTIVE", "COMPLETED")))).all()

    scale = grading.resolve_scale(db, school_id=school_id, band=grade.band,
                                  grade_id=grade.id, academic_year_id=academic_year_id)

    rows = []
    for enrollment, student in enrollments:
        scores_by_comp: dict[str, list[float]] = {}
        complete = True
        for comp in components:
            sheet = sheet_by_component.get(comp.id)
            score_row = None
            if sheet is not None:
                score_row = db.scalar(select(AssessmentScore).where(
                    AssessmentScore.assessment_id == sheet.id,
                    AssessmentScore.enrollment_id == enrollment.id))
            if score_row is None or score_row.raw_score is None:
                complete = False
                break
            scores_by_comp.setdefault(comp.code, []).append(float(score_row.raw_score))
        row = {"enrollment_id": str(enrollment.id), "student_id": str(student.id),
               "student_name": student.full_name, "admission_code": student.admission_code,
               "complete": complete, "final_score": None, "grade": None, "remark": None,
               "components": {}}
        if complete:
            final, comp_results = scoring.compute_final(specs, scores_by_comp)
            final = scoring.round_score(final, round_decimals)
            row["final_score"] = final
            row["components"] = {c.code: scoring.round_score(c.aggregate, round_decimals)
                                 for c in comp_results}
            if scale is not None:
                g = grading.grade_for_score(db, scale, final)
                if g:
                    row["grade"], row["remark"], row["grade_rank"] = g["grade"], g["remark"], g["rank"]
        rows.append(row)

    rows.sort(key=lambda r: (r["final_score"] is None,
                             -(r["final_score"] or 0), r["student_name"]))
    # optional class position (tie → same position, next skipped)
    pos, prev_score, prev_pos = 0, None, 0
    for r in rows:
        if r["final_score"] is None:
            r["position"] = None
            continue
        pos += 1
        if prev_score is not None and r["final_score"] == prev_score:
            r["position"] = prev_pos
        else:
            r["position"] = pos
            prev_pos = pos
        prev_score = r["final_score"]

    return {"scheme_id": str(scheme.id), "subject_id": str(subject_id),
            "components": [{"code": c.code, "name": c.name, "weight_pct": float(c.weight_pct)}
                           for c in components],
            "rows": rows}
