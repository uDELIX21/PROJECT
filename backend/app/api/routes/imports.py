"""Bulk import endpoints (REQ-IMP-*, design §10): templates, upload → preview →
resolve matches → confirm → report. Permission: IMPORT_DATA."""
import uuid

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import rbac
from app.api.deps import AuthContext, get_school, require
from app.core.db import get_db
from app.core.errors import ConflictError, NotFoundError
from app.core.ids import uuid7
from app.models.imports import ImportErrorRow, ImportJob
from app.schemas.requests import MatchResolveIn
from app.services import calendar, files as files_svc, imports as imp

router = APIRouter(prefix="/imports", tags=["imports"])

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_SUFFIXES = (".csv", ".xlsx")


# --- templates (registered BEFORE /{job_id} routes to avoid path capture) ---

@router.get("/templates/{kind}")
def download_template(kind: str, format: str = "csv",
                      ctx: AuthContext = Depends(require(rbac.IMPORT_DATA))):
    kind = kind.upper()
    if kind not in imp.TEMPLATES:
        raise NotFoundError("Unknown template kind.")
    if format == "xlsx":
        data = imp.template_xlsx(kind)
        mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        data = imp.template_csv(kind)
        mime = "text/csv"
    return Response(content=data, media_type=mime,
                    headers={"Content-Disposition":
                             f'attachment; filename="{kind.lower()}_template.{format}"'})


# --- job lifecycle ---

def _job_or_404(db: Session, school_id: uuid.UUID, job_id: uuid.UUID) -> ImportJob:
    j = db.get(ImportJob, job_id)
    if j is None or j.school_id != school_id:
        raise NotFoundError("Import job not found.")
    return j


@router.post("/upload", status_code=201)
async def upload(request: Request, file: UploadFile = File(...),
                 kind: str = Form(...),
                 ctx: AuthContext = Depends(require(rbac.IMPORT_DATA)),
                 db: Session = Depends(get_db)):
    school = get_school(db)
    kind = kind.upper()
    if kind not in imp.TEMPLATES:
        raise ConflictError("kind must be STUDENTS, TEACHERS or PARENTS.",
                            code="KIND_UNKNOWN")
    name = file.filename or "upload"
    if not name.lower().endswith(ALLOWED_SUFFIXES):
        raise ConflictError("Only .csv or .xlsx files are accepted.", code="FILE_TYPE_INVALID")
    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise ConflictError("File exceeds the 10 MB limit.", code="FILE_TOO_LARGE")
    year = calendar.active_year(db, school.id)
    if year is None:
        raise ConflictError("No active academic year.", code="NO_ACTIVE_YEAR")

    stored = files_svc.store_file(db, purpose="IMPORT_FILE", mime="text/csv",
                                  data=data, actor_id=ctx.user.id, key_hint=name[:40])
    job = ImportJob(id=uuid7(), school_id=school.id, kind=kind, file_id=stored.id,
                    file_name=name, options={"academic_year_id": str(year.id)},
                    created_by=ctx.user.id)
    db.add(job)
    db.flush()

    # Parse → Validate → Preview in one step (idempotent per upload)
    try:
        rows = imp.parse_file(kind, data, name)
    except ConflictError as e:
        job.stage = "FAILED"
        job.summary = {"error": e.message}
        db.flush()
        db.commit()
        raise
    job.rows_total = len(rows)
    findings = imp.validate_rows(db, school_id=school.id, kind=kind, rows=rows,
                                 year_id=year.id)
    counts = {"OK": 0, "WARNING": 0, "ERROR": 0, "DUPLICATE": 0, "MATCH_CANDIDATE": 0}
    for f in findings:
        counts[f["severity"]] += 1
        issues = f.get("issues") or ([{"severity": f["severity"], "field": None,
                                       "message": "", "guidance": None,
                                       "match": None}] if f["severity"] != "OK" else [])
        primary = issues[0] if issues else None
        db.add(ImportErrorRow(id=uuid7(), school_id=school.id, job_id=job.id,
                              row_no=f["row_no"], severity=f["severity"],
                              field=(primary or {}).get("field"),
                              message="; ".join(i["message"] for i in issues if i["message"]),
                              guidance=(primary or {}).get("guidance"),
                              raw_row=f["raw"],
                              match_suggestion=(primary or {}).get("match")))
    job.rows_ok = counts["OK"]
    job.rows_warn = counts["WARNING"]
    job.rows_error = counts["ERROR"]
    job.rows_duplicate = counts["DUPLICATE"]
    job.rows_match = counts["MATCH_CANDIDATE"]
    job.stage = "PREVIEWED"
    db.flush()
    db.commit()
    return {"job_id": str(job.id), "stage": job.stage, **{
        "rows_total": job.rows_total, "rows_ok": job.rows_ok,
        "rows_warning": job.rows_warn, "rows_error": job.rows_error,
        "rows_duplicate": job.rows_duplicate, "rows_match": job.rows_match}}


@router.get("/{job_id}/preview")
def preview(job_id: uuid.UUID, severity: str | None = None,
            ctx: AuthContext = Depends(require(rbac.IMPORT_DATA)),
            db: Session = Depends(get_db)):
    school = get_school(db)
    job = _job_or_404(db, school.id, job_id)
    stmt = select(ImportErrorRow).where(ImportErrorRow.job_id == job.id)
    if severity:
        stmt = stmt.where(ImportErrorRow.severity == severity.upper())
    rows = db.scalars(stmt.order_by(ImportErrorRow.row_no).limit(500)).all()
    return {"job": {"id": str(job.id), "kind": job.kind, "stage": job.stage,
                    "file_name": job.file_name, "rows_total": job.rows_total,
                    "rows_ok": job.rows_ok, "rows_warning": job.rows_warn,
                    "rows_error": job.rows_error, "rows_duplicate": job.rows_duplicate,
                    "rows_match": job.rows_match},
            "rows": [{"id": str(r.id), "row_no": r.row_no, "severity": r.severity,
                      "field": r.field, "message": r.message, "guidance": r.guidance,
                      "raw_row": r.raw_row,
                      "match_suggestion": r.match_suggestion} for r in rows]}


@router.post("/{job_id}/matches/{row_id}/resolve")
def resolve_match(job_id: uuid.UUID, row_id: uuid.UUID, body: MatchResolveIn,
                  request: Request,
                  ctx: AuthContext = Depends(require(rbac.IMPORT_DATA)),
                  db: Session = Depends(get_db)):
    """Confirm/reject a suggested parent link — links are NEVER created automatically."""
    school = get_school(db)
    job = _job_or_404(db, school.id, job_id)
    if job.stage != "PREVIEWED":
        raise ConflictError("Job already confirmed.", code="STAGE_INVALID")
    row = db.get(ImportErrorRow, row_id)
    if row is None or row.job_id != job.id:
        raise NotFoundError("Row not found.")
    if row.severity != "MATCH_CANDIDATE":
        raise ConflictError("Row has no pending match.", code="NO_MATCH")
    if body.action == "LINK" and not body.guardian_id:
        raise ConflictError("LINK requires guardian_id.", code="GUARDIAN_REQUIRED")
    suggestion = dict(row.match_suggestion or {})
    suggestion.update({"resolved": True, "action": body.action,
                       "guardian_id": str(body.guardian_id) if body.guardian_id else None,
                       "resolved_by": str(ctx.user.id)})
    row.match_suggestion = suggestion
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(row, "match_suggestion")
    from app.core.audit import audit
    audit(db, actor_id=ctx.user.id, action="import.match_resolved",
          entity_type="import_row", entity_id=row.id,
          new={"action": body.action,
               "guardian_id": str(body.guardian_id) if body.guardian_id else None},
          request=request)
    db.commit()
    return {"resolved": True, "action": body.action}


@router.post("/{job_id}/confirm")
def confirm(job_id: uuid.UUID, request: Request,
            ctx: AuthContext = Depends(require(rbac.IMPORT_DATA)),
            db: Session = Depends(get_db)):
    school = get_school(db)
    job = _job_or_404(db, school.id, job_id)
    result = imp.commit_job(db, job, actor_id=ctx.user.id, request=request)
    db.commit()
    if result.get("rolled_back"):
        raise ConflictError(
            f"Import rolled back — nothing was saved. ({result.get('error', '')[:160]})",
            code="IMPORT_ROLLED_BACK")
    return result


@router.get("/{job_id}")
def report(job_id: uuid.UUID, ctx: AuthContext = Depends(require(rbac.IMPORT_DATA)),
           db: Session = Depends(get_db)):
    school = get_school(db)
    job = _job_or_404(db, school.id, job_id)
    return {"id": str(job.id), "kind": job.kind, "stage": job.stage,
            "file_name": job.file_name, "summary": job.summary,
            "rows_total": job.rows_total, "rows_ok": job.rows_ok,
            "rows_warning": job.rows_warn, "rows_error": job.rows_error,
            "rows_duplicate": job.rows_duplicate, "rows_match": job.rows_match,
            "created_at": job.created_at.isoformat(),
            "finished_at": job.finished_at.isoformat() if job.finished_at else None}


@router.get("")
def history(ctx: AuthContext = Depends(require(rbac.IMPORT_DATA)),
            db: Session = Depends(get_db)):
    school = get_school(db)
    rows = db.scalars(select(ImportJob).where(ImportJob.school_id == school.id)
                      .order_by(ImportJob.created_at.desc()).limit(50)).all()
    return {"items": [{"id": str(j.id), "kind": j.kind, "stage": j.stage,
                       "file_name": j.file_name, "rows_total": j.rows_total,
                       "summary": j.summary,
                       "created_at": j.created_at.isoformat()} for j in rows]}
