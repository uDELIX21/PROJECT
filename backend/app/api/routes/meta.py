"""Bootstrap bundle & health checks (REQ-LOW-01: one small cached request)."""
from fastapi import APIRouter, Depends
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, current_user, get_school
from app.core.db import get_db, get_engine
from app.services import calendar

router = APIRouter(tags=["meta"])


@router.get("/meta/bootstrap")
def bootstrap(ctx: AuthContext = Depends(current_user), db: Session = Depends(get_db)):
    school = get_school(db)
    year = calendar.active_year(db, school.id)
    term = calendar.active_term(db, school.id)
    return {
        "school": {"id": str(school.id), "name": school.name, "motto": school.motto},
        "active_year": {"id": str(year.id), "name": year.name} if year else None,
        "active_term": {"id": str(term.id), "name": term.name} if term else None,
        "permissions": sorted(ctx.permissions),
        "roles": sorted(ctx.roles),
    }
