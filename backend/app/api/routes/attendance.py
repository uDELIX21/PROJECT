"""Attendance endpoints: sheets, summaries, compliance (REQ-ATT-*)."""
import uuid
from datetime import date

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import rbac
from app.api.deps import AuthContext, assert_stream_visible, get_school, require
from app.core.db import get_db
from app.core.errors import NotFoundError
from app.models.academic import AttendanceSheet
from app.schemas.requests import AttendanceSheetIn, SheetSubmitRefIn
from app.services import attendance as svc

router = APIRouter(prefix="/attendance", tags=["attendance"])


def _sheet_or_404(db: Session, school_id: uuid.UUID, sheet_id: uuid.UUID) -> AttendanceSheet:
    s = db.get(AttendanceSheet, sheet_id)
    if s is None or s.school_id != school_id:
        raise NotFoundError("Attendance sheet not found.")
    return s


@router.get("/sheets")
def get_sheet(class_stream_id: uuid.UUID, sheet_date: date,
              ctx: AuthContext = Depends(require(rbac.ENTER_MARKS)),
              db: Session = Depends(get_db)):
    school = get_school(db)
    assert_stream_visible(ctx, db, class_stream_id)
    sheet = svc.get_sheet(db, stream_id=class_stream_id, sheet_date=sheet_date)
    if sheet is None:
        return {"sheet": None, "records": []}
    records = svc.sheet_records(db, sheet.id)
    return {"sheet": {"id": str(sheet.id), "status": sheet.status,
                      "date": str(sheet.sheet_date)},
            "records": [{"enrollment_id": str(r.enrollment_id), "status": r.status,
                         "note": r.note} for r in records]}


@router.put("/sheets")
def save_sheet(body: AttendanceSheetIn, request: Request,
               ctx: AuthContext = Depends(require(rbac.ENTER_MARKS)),
               db: Session = Depends(get_db)):
    school = get_school(db)
    assert_stream_visible(ctx, db, body.class_stream_id)
    sheet = svc.upsert_sheet(db, school_id=school.id, stream_id=body.class_stream_id,
                             term_id=body.term_id, sheet_date=body.sheet_date,
                             records=[r.model_dump() for r in body.records],
                             actor_id=ctx.user.id, request=request)
    db.commit()
    return {"id": str(sheet.id), "status": sheet.status, "records": len(body.records)}


@router.post("/sheets/submit")
def submit_sheet(body: SheetSubmitRefIn, request: Request,
                 ctx: AuthContext = Depends(require(rbac.SUBMIT_MARKS)),
                 db: Session = Depends(get_db)):
    school = get_school(db)
    sheet = _sheet_or_404(db, school.id, body.sheet_id)
    assert_stream_visible(ctx, db, sheet.class_stream_id)
    svc.submit_sheet(db, sheet, actor_id=ctx.user.id, request=request)
    db.commit()
    return {"status": sheet.status}


@router.get("/summary")
def summary(class_stream_id: uuid.UUID, term_id: uuid.UUID,
            ctx: AuthContext = Depends(require(rbac.VIEW_STUDENT)),
            db: Session = Depends(get_db)):
    school = get_school(db)
    assert_stream_visible(ctx, db, class_stream_id)
    return svc.class_summary(db, class_stream_id, term_id)


@router.get("/student-summary")
def student_summary(enrollment_id: uuid.UUID,
                    ctx: AuthContext = Depends(require(rbac.VIEW_STUDENT)),
                    db: Session = Depends(get_db)):
    # scoped via enrollment → student visibility
    from app.models.core import Enrollment
    e = db.get(Enrollment, enrollment_id)
    if e is None:
        raise NotFoundError("Enrollment not found.")
    from app.api.deps import assert_student_visible
    assert_student_visible(ctx, db, e.student_id)
    return svc.student_summary(db, enrollment_id)


@router.get("/compliance")
def compliance(term_id: uuid.UUID,
               ctx: AuthContext = Depends(require(rbac.MANAGE_ATTENDANCE)),
               db: Session = Depends(get_db)):
    school = get_school(db)
    return {"items": svc.compliance(db, school_id=school.id, term_id=term_id)}
