"""Report cards: template-driven PDF generation, finalization, publication (BR-R).

PDF rendering is abstracted (design §17): WeasyPrintRenderer in production
(HTML/CSS templates), FpdfRenderer as the dependency-free fallback. Both consume
the same data snapshot built here.
"""
import uuid
from typing import Protocol

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import audit
from app.core.errors import ConflictError, NotFoundError
from app.core.ids import uuid7
from app.models.academic import (CompetencyRating, CoreCompetency, DevelopmentalDomain,
                                 DevelopmentalRating, ObservationLog, ReportCard,
                                 ReportTemplate)
from app.models.base import utcnow
from app.models.core import (AcademicYear, ClassStream, Enrollment, Grade, GradeSubject,
                             School, SchoolSetting, Student, Subject, Term)
from app.services import assessment, attendance, files, grading, scoring
from app.services import clearance as clearance_lib


# --------------------------------------------------------------------------- clearance stub

def evaluate_clearance(db: Session, *, school_id: uuid.UUID, student_id: uuid.UUID,
                       term_id: uuid.UUID, clearance_type: str = "REPORT_CARD") -> dict:
    """Financial clearance gate (REQ-CLR-01) — evaluated by the Phase-5 engine.
    An approved payment plan downgrades BLOCKED to PAYMENT_PLAN (still gating)."""
    from app.services import clearance
    result = clearance.evaluate(db, school_id=school_id, student_id=student_id,
                                term_id=term_id, clearance_type=clearance_type)
    if result["state"] == "BLOCKED" \
            and clearance.active_plan(db, student_id, term_id) is not None:
        result["state"] = "PAYMENT_PLAN"
    return result


# --------------------------------------------------------------------------- templates

DEFAULT_LAYOUTS = {
    "EARLY_CHILDHOOD": {"sections": ["developmental", "competencies", "observations",
                                     "attendance", "remarks"],
                        "show_positions": False},
    "PRIMARY": {"sections": ["academics", "competencies", "attendance", "remarks"],
                "show_positions": True, "show_grade_remarks": True},
    "JHS": {"sections": ["academics", "competencies", "attendance", "remarks"],
            "show_positions": True, "show_grade_remarks": True,
            "show_bece_note": True},
}


def ensure_default_templates(db: Session, school_id: uuid.UUID) -> None:
    for band, layout in DEFAULT_LAYOUTS.items():
        exists = db.scalar(select(ReportTemplate).where(
            ReportTemplate.school_id == school_id, ReportTemplate.band == band))
        if exists is None:
            db.add(ReportTemplate(id=uuid7(), school_id=school_id, band=band,
                                  name=f"{band.title().replace('_', ' ')} default",
                                  version=1, layout_config=layout, is_default=True))
    db.flush()


def template_for_band(db: Session, school_id: uuid.UUID, band: str) -> ReportTemplate:
    t = db.scalar(select(ReportTemplate).where(ReportTemplate.school_id == school_id,
                                               ReportTemplate.band == band,
                                               ReportTemplate.is_default.is_(True)))
    if t is None:
        raise ConflictError(f"No report template configured for band {band}.",
                            code="NO_TEMPLATE")
    return t


# --------------------------------------------------------------------------- data snapshot

def _setting(db: Session, school_id: uuid.UUID, key: str, default=None):
    row = db.scalar(select(SchoolSetting).where(SchoolSetting.school_id == school_id,
                                                SchoolSetting.key == key))
    return row.value if row is not None else default


def build_report_data(db: Session, *, school: School, student: Student, term: Term,
                      enrollment: Enrollment, grade: Grade, stream: ClassStream) -> dict:
    year = db.get(AcademicYear, term.academic_year_id)
    layout_band = grade.band
    data: dict = {
        "school": {"name": school.name, "motto": school.motto,
                   "digital_address": school.ghana_digital_address,
                   "phone": school.phone, "location": school.location},
        "student": {"name": student.full_name, "admission_code": student.admission_code,
                    "gender": student.gender, "date_of_birth": str(student.date_of_birth)},
        "class": {"stream": stream.name, "grade": grade.name, "band": layout_band},
        "year": year.name, "term": term.name,
        "attendance": attendance.student_summary(db, enrollment.id),
        "competencies": [],
        "subjects": [],
        "developmental": [],
        "observations": [],
        "positions_enabled": bool(_setting(db, school.id, "report_positions_enabled", True)),
        "round_decimals": int(_setting(db, school.id, "score_round_decimals", 1)),
    }
    for cr in db.execute(select(CompetencyRating, CoreCompetency)
                         .join(CoreCompetency,
                               CompetencyRating.competency_id == CoreCompetency.id)
                         .where(CompetencyRating.enrollment_id == enrollment.id,
                                CompetencyRating.term_id == term.id)):
        rating, comp = cr
        data["competencies"].append({"name": comp.name, "rating": rating.rating,
                                     "comment": rating.comment})

    if layout_band == "EARLY_CHILDHOOD":
        for dr in db.execute(select(DevelopmentalRating, DevelopmentalDomain)
                             .join(DevelopmentalDomain,
                                   DevelopmentalRating.domain_id == DevelopmentalDomain.id)
                             .where(DevelopmentalRating.enrollment_id == enrollment.id,
                                    DevelopmentalRating.term_id == term.id)):
            rating, domain = dr
            data["developmental"].append({"domain": domain.name, "rating": rating.rating,
                                          "comment": rating.comment})
        data["observations"] = [
            {"date": str(o.logged_on), "body": o.body}
            for o in db.scalars(select(ObservationLog)
                                .where(ObservationLog.enrollment_id == enrollment.id,
                                       ObservationLog.superseded_by.is_(None))
                                .order_by(ObservationLog.logged_on.desc()).limit(6))]
    else:
        grade_subjects = db.scalars(select(Subject).join(
            GradeSubject, GradeSubject.subject_id == Subject.id).where(
            GradeSubject.grade_id == grade.id)).all()
        for subject in grade_subjects:
            try:
                res = assessment.compute_stream_subject_results(
                    db, school_id=school.id, term_id=term.id,
                    class_stream_id=stream.id, subject_id=subject.id, grade=grade,
                    academic_year_id=term.academic_year_id,
                    round_decimals=data["round_decimals"])
            except ConflictError:
                continue  # subject without scheme this term: skipped, not fatal
            mine = next((r for r in res["rows"] if r["student_id"] == str(student.id)), None)
            if mine is None:
                continue
            data["subjects"].append({
                "name": subject.name,
                "components": res["components"],
                "component_scores": mine.get("components", {}),
                "final_score": mine.get("final_score"),
                "grade": mine.get("grade"),
                "remark": mine.get("remark"),
                "position": mine.get("position"),
                "class_size": len(res["rows"]),
            })
    return data


# --------------------------------------------------------------------------- PDF renderers

class PdfRenderer(Protocol):
    def render_report(self, data: dict, template: ReportTemplate) -> bytes: ...


class FpdfRenderer:
    """Dependency-free renderer (fpdf2) — structured, printable, template-driven."""

    _TRANSLATE = {
        "\u2014": "-", "\u2013": "-", "\u2018": "'", "\u2019": "'",
        "\u201c": '"', "\u201d": '"', "\u00b7": "-", "\u2026": "...",
    }

    @classmethod
    def _t(cls, value) -> str:
        """Core PDF fonts are latin-1; normalize unicode punctuation safely."""
        if value is None:
            return ""
        s = str(value)
        for k, v in cls._TRANSLATE.items():
            s = s.replace(k, v)
        return s.encode("latin-1", errors="replace").decode("latin-1")

    def render_report(self, data: dict, template: ReportTemplate) -> bytes:
        from fpdf import FPDF

        layout = template.layout_config or {}
        sections = set(layout.get("sections", []))
        show_positions = data.get("positions_enabled", False) and layout.get("show_positions", False)

        pdf = FPDF(format="A4")
        pdf.set_auto_page_break(auto=True, margin=14)
        pdf.add_page()
        pdf.set_margins(12, 10, 12)

        # header
        pdf.set_font("Helvetica", "B", 15)
        pdf.cell(0, 7, self._t(data["school"]["name"]), align="C", new_x="LMARGIN", new_y="NEXT")
        if data["school"].get("motto"):
            pdf.set_font("Helvetica", "I", 9)
            pdf.cell(0, 5, self._t(data["school"]["motto"]), align="C", new_x="LMARGIN", new_y="NEXT")
        contact = " · ".join(x for x in (data["school"].get("location"),
                                         data["school"].get("phone"),
                                         data["school"].get("digital_address")) if x)
        if contact:
            pdf.set_font("Helvetica", "", 8)
            pdf.cell(0, 4, self._t(contact), align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "B", 11)
        band_title = {"EARLY_CHILDHOOD": "Early Childhood", "PRIMARY": "Primary",
                      "JHS": "Junior High School"}[data["class"]["band"]]
        pdf.cell(0, 8, self._t(f"{band_title} Terminal Report — {data['term']} {data['year']}"),
                 align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

        # student info
        s = data["student"]
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, self._t(f"Name: {s['name']}    Class: {data['class']['stream']}"
                       f"    Code: {s['admission_code']}    Gender: {s['gender']}"),
                 new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

        if "academics" in sections and data["subjects"]:
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 7, "Academic Performance", new_x="LMARGIN", new_y="NEXT")
            comp_cols = max(len(sub["components"]) for sub in data["subjects"])
            widths = [52] + [22] * comp_cols + [20, 14] + ([26] if show_positions else []) + [30]
            pdf.set_font("Helvetica", "B", 8)
            headers = ["Subject"] + [c["code"].replace("_", " ")[:12] for c in
                                     data["subjects"][0]["components"]]
            headers += ["Total", "Grade"] + (["Pos."] if show_positions else []) + ["Remark"]
            for i, h in enumerate(headers):
                pdf.cell(widths[i], 6, h, border=1)
            pdf.ln()
            pdf.set_font("Helvetica", "", 8)
            for sub in data["subjects"]:
                pdf.cell(widths[0], 6, self._t(sub["name"][:30]), border=1)
                for i, c in enumerate(sub["components"]):
                    v = sub["component_scores"].get(c["code"])
                    pdf.cell(widths[1 + i], 6, f"{v:.1f}" if isinstance(v, (int, float)) else "-",
                             border=1, align="R")
                # pad missing component columns
                for i in range(len(sub["components"]), comp_cols):
                    pdf.cell(widths[1 + i], 6, "", border=1)
                total = sub["final_score"]
                pdf.cell(widths[1 + comp_cols], 6,
                         f"{total:.1f}" if isinstance(total, (int, float)) else "-",
                         border=1, align="R")
                pdf.cell(widths[2 + comp_cols], 6, sub.get("grade") or "-", border=1, align="C")
                if show_positions:
                    pos = sub.get("position")
                    pdf.cell(widths[3 + comp_cols], 6,
                             f"{pos}/{sub.get('class_size') or '-'}" if pos else "-",
                             border=1, align="C")
                pdf.cell(widths[-1], 6, self._t((sub.get("remark") or "")[:16]), border=1)
                pdf.ln()
            pdf.ln(3)

        if "developmental" in sections and data["developmental"]:
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 7, "Developmental Assessment", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 9)
            pdf.cell(70, 6, "Domain", border=1)
            pdf.cell(35, 6, "Rating", border=1)
            pdf.cell(80, 6, "Comment", border=1)
            pdf.ln()
            for d in data["developmental"]:
                pdf.cell(70, 6, self._t(d["domain"][:38]), border=1)
                pdf.cell(35, 6, d["rating"].title(), border=1, align="C")
                pdf.cell(80, 6, self._t((d.get("comment") or "")[:52]), border=1)
                pdf.ln()
            pdf.ln(3)

        if "observations" in sections and data["observations"]:
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 7, "Recent Observations", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 8)
            for o in data["observations"]:
                pdf.multi_cell(0, 4.5, self._t(f"[{o['date']}] {o['body'][:220]}"))
            pdf.ln(2)

        if "competencies" in sections and data["competencies"]:
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 7, "Core Competencies", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 9)
            for c in data["competencies"]:
                pdf.cell(70, 6, self._t(c["name"]), border=1)
                pdf.cell(35, 6, c["rating"].title(), border=1, align="C")
                pdf.cell(80, 6, self._t((c.get("comment") or "")[:52]), border=1)
                pdf.ln()
            pdf.ln(3)

        if "attendance" in sections:
            a = data["attendance"]
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 7, "Attendance", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 9)
            counts = a.get("counts", {})
            txt = (f"Days recorded: {a.get('days_recorded', 0)}   Present: {counts.get('PRESENT', 0)}"
                   f"   Late: {counts.get('LATE', 0)}   Absent: {counts.get('ABSENT', 0)}"
                   f"   Excused: {counts.get('EXCUSED', 0)}"
                   f"   Attendance: {a.get('percentage') if a.get('percentage') is not None else '-'}%")
            pdf.cell(0, 6, self._t(txt), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(3)

        if "remarks" in sections:
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 7, "Remarks", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 9)
            pdf.cell(35, 6, "Class teacher:")
            pdf.cell(0, 6, self._t(str(data.get("teacher_remark") or "")[:90]),
                     new_x="LMARGIN", new_y="NEXT")
            pdf.cell(35, 6, "Head teacher:")
            pdf.cell(0, 6, self._t(str(data.get("head_remark") or "")[:90]),
                     new_x="LMARGIN", new_y="NEXT")
            pdf.ln(6)
            pdf.cell(60, 6, "Class Teacher's Signature: ____________________")
            pdf.cell(20)
            pdf.cell(60, 6, "Head Teacher's Signature: ____________________")

        if layout.get("show_bece_note") and data["class"]["band"] == "JHS":
            pdf.ln(8)
            pdf.set_font("Helvetica", "I", 7)
            pdf.multi_cell(0, 3.5, self._t(
                           "Any BECE-style grade shown by the school is a school assessment, "
                           "not an official BECE result."))

        return bytes(pdf.output())


class WeasyPrintRenderer:
    """Production renderer: Jinja2 HTML template → WeasyPrint (CSS-driven layout)."""

    def __init__(self, template_dir: str = "app/templates/reports"):
        self.template_dir = template_dir

    def render_report(self, data: dict, template: ReportTemplate) -> bytes:
        import weasyprint  # lazy: requires system pango (production hosts)
        from jinja2 import Environment, FileSystemLoader
        env = Environment(loader=FileSystemLoader(self.template_dir), autoescape=True)
        tpl = env.get_template(f"report_{data['class']['band'].lower()}.html")
        html = tpl.render(data=data, layout=template.layout_config or {})
        return weasyprint.HTML(string=html).write_pdf()


def get_pdf_renderer() -> PdfRenderer:
    """WeasyPrint when available (prod), fpdf2 fallback otherwise (dev/test)."""
    try:
        import weasyprint  # noqa: F401
        return WeasyPrintRenderer()
    except Exception:
        return FpdfRenderer()


# --------------------------------------------------------------------------- lifecycle

def _get_parts(db: Session, school_id: uuid.UUID, student_id: uuid.UUID, term_id: uuid.UUID):
    student = db.get(Student, student_id)
    term = db.get(Term, term_id)
    if student is None or student.school_id != school_id or term is None \
            or term.school_id != school_id:
        raise NotFoundError("Student or term not found.")
    enrollment = db.scalar(select(Enrollment).where(
        Enrollment.student_id == student_id, Enrollment.academic_year_id == term.academic_year_id,
        Enrollment.status.in_(("ACTIVE", "COMPLETED"))).limit(1))
    if enrollment is None:
        raise ConflictError("Student has no enrollment for the report's academic year.",
                            code="NO_ENROLLMENT")
    stream = db.get(ClassStream, enrollment.class_stream_id)
    grade = db.get(Grade, stream.grade_id)
    return student, term, enrollment, stream, grade


def get_or_create_report(db: Session, *, school: School, student_id: uuid.UUID,
                         term_id: uuid.UUID) -> ReportCard:
    report = db.scalar(select(ReportCard).where(ReportCard.student_id == student_id,
                                                ReportCard.term_id == term_id,
                                                ReportCard.school_id == school.id))
    if report is None:
        _s, term, enrollment, stream, grade = _get_parts(db, school.id, student_id, term_id)
        template = template_for_band(db, school.id, grade.band)
        report = ReportCard(id=uuid7(), school_id=school.id, student_id=student_id,
                            term_id=term_id, template_id=template.id)
        db.add(report)
        db.flush()
    return report


def generate_report(db: Session, *, school: School, student_id: uuid.UUID, term_id: uuid.UUID,
                    actor_id: uuid.UUID, teacher_remark: str | None = None,
                    head_remark: str | None = None,
                    request: Request | None = None) -> ReportCard:
    report = get_or_create_report(db, school=school, student_id=student_id, term_id=term_id)
    if report.status == "FINALIZED" or report.status == "PUBLISHED":
        raise ConflictError(
            "Report is finalized; regeneration requires an authorized override (BR-R03).",
            code="REPORT_FINALIZED")
    student, term, enrollment, stream, grade = _get_parts(db, school.id, student_id, term_id)
    data = build_report_data(db, school=school, student=student, term=term,
                             enrollment=enrollment, grade=grade, stream=stream)
    data["teacher_remark"] = teacher_remark if teacher_remark is not None else report.teacher_remark
    data["head_remark"] = head_remark if head_remark is not None else report.head_remark
    if teacher_remark is not None:
        report.teacher_remark = teacher_remark
    if head_remark is not None:
        report.head_remark = head_remark

    pdf_bytes = get_pdf_renderer().render_report(data, db.get(ReportTemplate, report.template_id))
    stored = files.store_file(db, purpose="REPORT_CARD", mime="application/pdf",
                              data=pdf_bytes, actor_id=actor_id,
                              key_hint=student.admission_code)
    report.data_snapshot = data
    report.pdf_file_id = stored.id
    report.status = "GENERATED"
    audit(db, actor_id=actor_id, action="report.generated", entity_type="report_card",
          entity_id=report.id, new={"student": student.admission_code, "term": term.name},
          request=request)
    db.flush()
    return report


def finalize_report(db: Session, report: ReportCard, *, actor_id: uuid.UUID,
                    request: Request | None = None) -> ReportCard:
    if report.status not in ("GENERATED",):
        raise ConflictError("Only generated reports can be finalized.", code="NOT_GENERATED")
    report.status = "FINALIZED"
    report.finalized_by = actor_id
    report.finalized_at = utcnow()
    audit(db, actor_id=actor_id, action="report.finalized", entity_type="report_card",
          entity_id=report.id, request=request)
    db.flush()
    return report


def publish_report(db: Session, report: ReportCard, *, actor_id: uuid.UUID,
                   override_reason: str | None = None,
                   request: Request | None = None) -> ReportCard:
    if report.status not in ("GENERATED", "FINALIZED"):
        raise ConflictError("Report must be generated before publishing.", code="NOT_GENERATED")
    clearance = evaluate_clearance(db, school_id=report.school_id,
                                   student_id=report.student_id, term_id=report.term_id)
    state = clearance.get("state", "BLOCKED")
    if state not in clearance_lib.PASS_STATES:
        raise ConflictError("Financial clearance blocks publication of this report (BR-R02).",
                            code="CLEARANCE_BLOCKED")
    # a waiver/override needs a reason — either recorded earlier with the override
    # itself, or supplied now alongside the publication
    if state in ("WAIVED", "MANUAL_OVERRIDE") \
            and not (override_reason or clearance.get("override_reason")):
        raise ConflictError("A reason is required for clearance overrides.",
                            code="REASON_REQUIRED")
    report.clearance_snapshot = clearance
    report.status = "PUBLISHED"
    report.published_at = utcnow()
    report.override_reason = override_reason
    audit(db, actor_id=actor_id, action="report.published", entity_type="report_card",
          entity_id=report.id, new={"clearance": state}, reason=override_reason,
          request=request)
    # communications event: report availability to guardians (REQ-COM-01)
    try:
        from app.models.core import School, Student, Term
        from app.services import comms as comms_svc
        school = db.get(School, report.school_id)
        student = db.get(Student, report.student_id)
        term = db.get(Term, report.term_id)
        if school and student and term:
            comms_svc.report_available_comms(db, school_id=report.school_id,
                                             school_name=school.name, student=student,
                                             term_name=term.name)
    except Exception:
        pass
    db.flush()
    return report
