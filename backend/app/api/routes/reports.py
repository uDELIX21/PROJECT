"""Report card endpoints: templates, generate, PDF, finalize, publish (REQ-RPT-*)."""
import uuid

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import rbac
from app.api.deps import (AuthContext, assert_student_visible, get_school, require,
                          student_scope)
from app.core.db import get_db
from app.core.errors import ConflictError, ForbiddenError, NotFoundError
from app.models.academic import ReportCard, ReportTemplate
from app.schemas.requests import ReportGenerateIn, ReportPublishIn, TemplatePutIn
from app.services import files as files_svc
from app.services import reports as svc

router = APIRouter(prefix="/reports", tags=["reports"])


def _report_or_404(db: Session, school_id: uuid.UUID, report_id: uuid.UUID) -> ReportCard:
    r = db.get(ReportCard, report_id)
    if r is None or r.school_id != school_id:
        raise NotFoundError("Report not found.")
    return r


@router.get("/templates")
def list_templates(ctx: AuthContext = Depends(require(rbac.VIEW_GRADES_CONFIG)),
                   db: Session = Depends(get_db)):
    school = get_school(db)
    rows = db.scalars(select(ReportTemplate).where(
        ReportTemplate.school_id == school.id)).all()
    return {"items": [{"id": str(t.id), "band": t.band, "name": t.name,
                       "version": t.version, "layout_config": t.layout_config,
                       "is_default": t.is_default} for t in rows]}


@router.put("/templates/{template_id}")
def put_template(template_id: uuid.UUID, body: TemplatePutIn, request: Request,
                 ctx: AuthContext = Depends(require(rbac.MANAGE_REPORTS)),
                 db: Session = Depends(get_db)):
    school = get_school(db)
    t = db.get(ReportTemplate, template_id)
    if t is None or t.school_id != school.id:
        raise NotFoundError("Template not found.")
    if body.layout_config is not None:
        t.layout_config = body.layout_config
    if body.name is not None:
        t.name = body.name
    t.updated_by = ctx.user.id
    db.commit()
    return {"id": str(t.id), "layout_config": t.layout_config}


@router.post("/generate", status_code=201)
def generate(body: ReportGenerateIn, request: Request,
             ctx: AuthContext = Depends(require(rbac.MANAGE_REPORTS)),
             db: Session = Depends(get_db)):
    school = get_school(db)
    report = svc.generate_report(db, school=school, student_id=body.student_id,
                                 term_id=body.term_id, actor_id=ctx.user.id,
                                 teacher_remark=body.teacher_remark,
                                 head_remark=body.head_remark, request=request)
    db.commit()
    return {"id": str(report.id), "status": report.status}


@router.post("/{report_id}/finalize")
def finalize(report_id: uuid.UUID, request: Request,
             ctx: AuthContext = Depends(require(rbac.MANAGE_REPORTS)),
             db: Session = Depends(get_db)):
    school = get_school(db)
    report = svc.finalize_report(db, _report_or_404(db, school.id, report_id),
                                 actor_id=ctx.user.id, request=request)
    db.commit()
    return {"status": report.status}


@router.post("/{report_id}/publish")
def publish(report_id: uuid.UUID, body: ReportPublishIn, request: Request,
            ctx: AuthContext = Depends(require(rbac.MANAGE_REPORTS)),
            db: Session = Depends(get_db)):
    school = get_school(db)
    report = svc.publish_report(db, _report_or_404(db, school.id, report_id),
                                actor_id=ctx.user.id, override_reason=body.override_reason,
                                request=request)
    db.commit()
    return {"status": report.status, "clearance": report.clearance_snapshot}


@router.get("")
def list_reports(term_id: uuid.UUID, student_id: uuid.UUID | None = None,
                 ctx: AuthContext = Depends(require(rbac.VIEW_REPORT)),
                 db: Session = Depends(get_db)):
    school = get_school(db)
    stmt = select(ReportCard).where(ReportCard.school_id == school.id,
                                    ReportCard.term_id == term_id)
    if student_id:
        assert_student_visible(ctx, db, student_id)
        stmt = stmt.where(ReportCard.student_id == student_id)
    rows = db.scalars(stmt).all()
    # parents/students: only PUBLISHED reports, and only their own children (BR-R04)
    if ctx.user.parent_id is not None or ctx.user.student_id is not None:
        scope = student_scope(ctx, db)
        rows = [r for r in rows
                if r.status == "PUBLISHED" and (scope is None or r.student_id in scope)]
    return {"items": [{"id": str(r.id), "student_id": str(r.student_id),
                       "status": r.status, "published_at": r.published_at.isoformat()
                       if r.published_at else None} for r in rows]}


@router.get("/{report_id}/pdf")
def download_pdf(report_id: uuid.UUID,
                 ctx: AuthContext = Depends(require(rbac.VIEW_REPORT)),
                 db: Session = Depends(get_db)):
    school = get_school(db)
    report = _report_or_404(db, school.id, report_id)
    assert_student_visible(ctx, db, report.student_id)
    # parents/students: published only (BR-R04); staff: any generated+ state
    if (ctx.user.parent_id is not None or ctx.user.student_id is not None) \
            and report.status != "PUBLISHED":
        raise NotFoundError("Report not found.")  # uniform — not "not published"
    if report.pdf_file_id is None:
        raise ConflictError("Report has not been generated yet.", code="NOT_GENERATED")
    stored, data = files_svc.read_file(report.pdf_file_id, db)
    return Response(content=data, media_type="application/pdf",
                    headers={"Content-Disposition":
                             f'inline; filename="report-{report_id}.pdf"'})
