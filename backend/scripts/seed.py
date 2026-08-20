"""Deterministic synthetic seed data — 100% fictional (REQ-SEED-02, Agent Rule 12).

Usage:
  python scripts/seed.py                 # full demo (~700 students, 20 streams)
  python scripts/seed.py --fast          # small dev set (~60 students, 6 streams)
  python scripts/seed.py --reset         # drop & recreate schema first
"""
import argparse
import os
import random
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from faker import Faker  # noqa: E402
from sqlalchemy import select, text  # noqa: E402

from app import rbac  # noqa: E402
from app.core import security  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.core.db import get_engine, get_session_factory, reset_engine_cache  # noqa: E402
from app.core.ids import uuid7  # noqa: E402
from app.core.phones import normalize_ghana_phone  # noqa: E402
from app.models import Base  # noqa: E402
from app.models.auth import Role, User, UserRole  # noqa: E402
from app.models.core import (AcademicYear, ClassStream, Enrollment, Grade,  # noqa: E402
                             ParentGuardian, ParentStudentRelationship, School,
                             Student, Teacher, TeacherAssignment, Term)
from app.services import catalog  # noqa: E402

SEED = 20260820  # deterministic RNG — reproducible demo data
DEMO_PASSWORD = "Demo#2026accra"  # printed once; demo-only credentials

fake = Faker("en_GB")  # Ghana locale not in faker; addresses are demo filler anyway
Faker.seed(SEED)
rng = random.Random(SEED)

# Ghanaian-flavoured fictional name pools
SURNAMES = ["Mensah", "Owusu", "Boateng", "Asante", "Osei", "Adjei", "Ampofo", "Quartey",
            "Tetteh", "Ankrah", "Appiah", "Agyeman", "Darko", "Ofori", "Amoah", "Baah",
            "Danso", "Frimpong", "Gyasi", "Kusi", "Marfo", "Ntim", "Owusua", "Sarpong"]
OTHER_NAMES_F = ["Abena", "Adwoa", "Akosua", "Ama", "Afia", "Esi", "Yaa", "Efua", "Kofi",
                 "Mansa", "Araba", "Adjoa"]
OTHER_NAMES_M = ["Kwame", "Kofi", "Kwabena", "Kwaku", "Yaw", "Kwesi", "Kojo", "Kwabena",
                 "Emmanuel", "Daniel", "Samuel", "Isaac"]
STAFF_SURNAMES = SURNAMES[:15]


def seed_finance(db, school, grades, year_cur, terms_cur, admin):
    """Phase-5 financial demo data: structures (spec §19 amounts as config rows),
    billing, mixed payment history, waivers, plans, clearance policies."""
    from datetime import timedelta as _td

    from app.models.core import ClassStream, Enrollment
    from app.models.finance import FeeStructure, Payment
    from app.services import clearance, fees, ledger, payments

    exists = db.scalar(select(FeeStructure).where(
        FeeStructure.school_id == school.id).limit(1))
    if exists is not None:
        print("[seed] finance already present — skipping finance stage")
        return

    term1 = terms_cur[0]
    payments.ensure_default_providers(db, school.id)

    # fee structures per grade — initial tuition values from spec §19 (config, not code)
    for code, g in grades.items():
        if g.band == "EARLY_CHILDHOOD":
            items = [{"fee_type": "TUITION", "display_name": "Tuition",
                      "amount_pesewas": rng.randint(30000, 35000), "period": "PER_TERM"},
                     {"fee_type": "FEEDING", "display_name": "Feeding",
                      "amount_pesewas": 10000, "period": "PER_TERM"}]
        elif g.band == "PRIMARY":
            amount = 40000 if g.ordinal <= 8 else 50000  # B1–3 vs B4–6
            items = [{"fee_type": "TUITION", "display_name": "Tuition",
                      "amount_pesewas": amount, "period": "PER_TERM"},
                     {"fee_type": "PTA_LEVY", "display_name": "PTA Levy",
                      "amount_pesewas": 2000, "period": "PER_TERM"}]
        else:
            items = [{"fee_type": "TUITION", "display_name": "Tuition",
                      "amount_pesewas": 60000, "period": "PER_TERM"},
                     {"fee_type": "ICT_LAB", "display_name": "ICT Lab",
                      "amount_pesewas": 5000, "period": "PER_TERM"}]
        fees.create_structure(db, school_id=school.id, academic_year_id=year_cur.id,
                              name=f"{g.name} fees", grade_id=g.id, items=items,
                              actor_id=admin.id)

    billed = fees.apply_billing(db, school_id=school.id, academic_year_id=year_cur.id,
                                term_id=term1.id, actor_id=admin.id)

    # opening debts for a small subset (import-style OPENING_BALANCE entries)
    enrollments = db.scalars(select(Enrollment).where(
        Enrollment.academic_year_id == year_cur.id,
        Enrollment.status == "ACTIVE")).all()
    opening = 0
    for e in rng.sample(enrollments, max(1, len(enrollments) // 12)):
        ledger.post(db, school_id=school.id, student_id=e.student_id,
                    academic_year_id=year_cur.id, entry_type="DEBIT",
                    category="OPENING_BALANCE",
                    amount_pesewas=rng.randint(8000, 45000),
                    occurred_on=year_cur.starts_on,
                    description="Opening balance (carried forward)",
                    idempotency_key=f"opening:{e.id}", actor_id=admin.id, quiet=True)
        opening += 1

    # payment history: ~40% full, ~30% partial, rest unpaid; mixed methods
    methods = ["CASH", "MTN_MOMO", "TELECEL_CASH", "AT_MONEY"]
    paid_full = paid_partial = 0
    charged_students = {}
    for e in enrollments:
        totals = ledger.term_totals(db, e.student_id, term1.id)
        if totals["charged_pesewas"] > 0:
            charged_students[e.student_id] = (e, totals["charged_pesewas"])
    for sid, (e, charged) in charged_students.items():
        roll = rng.random()
        if roll < 0.40:
            amount = charged
            paid_full += 1
        elif roll < 0.70:
            amount = int(charged * rng.uniform(0.3, 0.8))
            paid_partial += 1
        else:
            continue
        method = rng.choice(methods)
        payment = payments.initiate_payment(
            db, school=school, school_id=school.id, student_id=sid,
            amount_pesewas=amount, method=method, term_id=term1.id,
            actor_id=admin.id)
        if payment.status == "PENDING":  # e-money stubs: confirm deterministically
            payments.confirm_payment(db, payment, actor_id=admin.id, quiet_audit=True)

    # scholarships/waivers for a handful of students
    waived = 0
    for sid, (e, charged) in rng.sample(list(charged_students.items()), 6):
        fees.grant_waiver(db, school_id=school.id, enrollment=e, kind="SCHOLARSHIP",
                          amount_pesewas=None, pct=50.0,
                          reason="Mission scholarship — seeded demo data.",
                          approver_id=admin.id, term_id=term1.id)
        waived += 1

    # two payment plans
    plans = 0
    for sid, (e, charged) in rng.sample(list(charged_students.items()), 2):
        fees.create_plan(db, school_id=school.id, enrollment=e, term_id=term1.id,
                         installments=[
                             {"due_on": term1.starts_on, "amount_pesewas": charged // 3},
                             {"due_on": term1.starts_on + _td(days=30),
                              "amount_pesewas": charged // 3},
                             {"due_on": term1.starts_on + _td(days=60),
                              "amount_pesewas": charged - 2 * (charged // 3)}],
                         approver_id=admin.id, note="Agreed instalment plan (demo)")
        plans += 1

    # one reversed payment for the reconciliation demo
    sample = rng.choice(list(charged_students.values()))
    payment = payments.initiate_payment(
        db, school=school, school_id=school.id, student_id=sample[0].student_id,
        amount_pesewas=5000, method="MTN_MOMO", term_id=term1.id, actor_id=admin.id)
    if payment.status == "PENDING":
        payments.confirm_payment(db, payment, actor_id=admin.id, quiet_audit=True)
    payments.reverse_payment(db, payment, reason="Provider reversal (demo reconciliation)",
                             actor_id=admin.id)

    # clearance policies: report cards ≥ 70% paid, exams ≥ 100% (config rows)
    clearance.create_policy(db, school_id=school.id, academic_year_id=year_cur.id,
                            term_id=term1.id, clearance_type="REPORT_CARD",
                            mode="PERCENT_OF_CHARGES", threshold=7000,
                            actor_id=admin.id)
    clearance.create_policy(db, school_id=school.id, academic_year_id=year_cur.id,
                            term_id=term1.id, clearance_type="EXAMINATION",
                            mode="PERCENT_OF_CHARGES", threshold=10000,
                            actor_id=admin.id)

    from sqlalchemy import func as _func
    confirmed = db.scalar(select(_func.count()).select_from(Payment).where(
        Payment.school_id == school.id, Payment.status == "CONFIRMED"))
    print(f"[seed] finance: billed {billed['created']} charges, {opening} opening debts, "
          f"{paid_full} full + {paid_partial} partial payments ({confirmed} confirmed), "
          f"{waived} scholarships, {plans} payment plans, 1 reversal")


def seed_operations(db, school, year_cur, terms_cur, teachers, students, admin):
    """Phase-6 demo data: appraisal criteria+appraisals, discipline incidents,
    pickup authorizations, comms templates + one announcement."""
    from app.models.operations import PickupAuthorization
    from app.services import appraisals, comms, discipline, pickup

    if db.scalar(select(PickupAuthorization).where(
            PickupAuthorization.school_id == school.id).limit(1)) is not None:
        print("[seed] operations already present — skipping operations stage")
        return

    term1 = terms_cur[0]
    appraisals.bootstrap_criteria(db, school.id)
    comms.ensure_default_templates(db, school.id)
    db.flush()

    # appraisals: a handful of teachers, submitted/acknowledged mix
    criteria = appraisals.criteria_for(db, school.id)
    n_appraisals = 0
    for t in teachers[:6]:
        a = appraisals.create_appraisal(db, school_id=school.id, teacher_id=t.id,
                                        evaluator_user_id=admin.id,
                                        period_from=term1.starts_on,
                                        period_to=term1.ends_on)
        appraisals.save_scores(db, a, [
            {"criterion_id": c.id, "score": rng.randint(6, c.max_score),
             "comment": rng.choice(["Consistent.", "Improving.", "Excellent practice.", None])}
            for c in criteria], actor_id=admin.id)
        appraisals.submit_appraisal(db, a, actor_id=admin.id,
                                    overall_comment="Seeded demo appraisal.")
        if rng.random() < 0.5:
            appraisals.acknowledge_appraisal(db, a, actor_id=admin.id)
        n_appraisals += 1

    # discipline incidents: mixed categories/statuses
    n_incidents = 0
    for s in rng.sample(students, 8):
        status = rng.choice(["OPEN", "UNDER_REVIEW", "RESOLVED", "RESOLVED"])
        category = rng.choice(discipline.CATEGORIES)
        inc = discipline.create_incident(
            db, school_id=school.id, student_id=s.id, category=category,
            description=rng.choice([
                "Disrupted group work despite two verbal warnings.",
                "Damaged a classroom poster during break.",
                "Arrived late three times this week.",
                "Used inappropriate language towards a classmate."]),
            staff_user_id=admin.id, severity=rng.choice(["MINOR", "MINOR", "MODERATE"]))
        if status == "RESOLVED":
            discipline.update_status(db, inc, status="RESOLVED",
                                     resolution="Parent contacted; agreed follow-up.",
                                     action_taken="Counselling session", actor_id=admin.id)
        else:
            discipline.update_status(db, inc, status=status, resolution=None,
                                     action_taken=None, actor_id=admin.id)
        n_incidents += 1

    # pickup authorizations for early-childhood students
    ec_students = [s for s in students if s.date_of_birth.year >= 2020]
    n_pickup = 0
    for s in rng.sample(ec_students, min(30, len(ec_students))):
        pickup.create_authorization(
            db, school_id=school.id, student_id=s.id,
            person_name=f"{rng.choice(SURNAMES)} {rng.choice(OTHER_NAMES_F)}",
            relationship=rng.choice(["GRANDMOTHER", "AUNT", "UNCLE", "NANNY"]),
            phone=rand_phone(), id_reference=None,
            expires_on=year_cur.ends_on.date() if hasattr(year_cur.ends_on, "date") else year_cur.ends_on,
            actor_id=admin.id)
        n_pickup += 1

    # a welcome announcement notification for parent logins
    from app.models.auth import User
    parent_users = db.scalars(select(User).where(User.parent_id.isnot(None),
                                                 User.status == "ACTIVE").limit(20)).all()
    for u in parent_users:
        comms.notify_user(db, school_id=school.id, user_id=u.id, kind="ANNOUNCEMENT",
                          title="Welcome to the new term",
                          body="The 2026/2027 academic year has begun. Fees, reports and "
                               "announcements are now available in this portal.")
    db.flush()
    print(f"[seed] operations: {n_appraisals} appraisals, {n_incidents} discipline incidents, "
          f"{n_pickup} pickup authorizations, {len(parent_users)} notifications")


def rand_phone() -> str:
    prefix = rng.choice(["24", "20", "27", "50", "54", "55", "26"])
    return f"+233{prefix}{rng.randint(1000000, 9999999)}"


def seed_academics(db, school, roles, grades, year_cur, terms_cur, streams, students,
                   teachers, admin, settings):
    """Phase-4 academic data: scales, schemes, marks, attendance, ECD, reports."""
    from datetime import timedelta as _td

    from app.models.academic import (AssessmentScheme, CoreCompetency, Curriculum,
                                     Indicator)
    from app.models.core import Enrollment, Grade as GradeM, Subject
    from app.services import assessment as assess
    from app.services import attendance as att
    from app.services import curriculum as curr
    from app.services import ecd, grading, reports

    exists = db.scalar(select(AssessmentScheme).where(
        AssessmentScheme.school_id == school.id).limit(1))
    if exists is not None:
        print("[seed] academics already present — skipping academic stage")
        return

    term1 = terms_cur[0]
    curr.bootstrap_catalogs(db, school.id)
    reports.ensure_default_templates(db, school.id)
    db.flush()

    # --- grading scales (configuration rows, not code — REQ-GRD-01) ---
    primary_bands = [
        {"min_score": 80, "max_score": 100, "code": "A", "remark": "Excellent", "rank": 1},
        {"min_score": 70, "max_score": 79.99, "code": "B", "remark": "Very Good", "rank": 2},
        {"min_score": 60, "max_score": 69.99, "code": "C", "remark": "Good", "rank": 3},
        {"min_score": 50, "max_score": 59.99, "code": "D", "remark": "Credit", "rank": 4},
        {"min_score": 40, "max_score": 49.99, "code": "E", "remark": "Pass", "rank": 5},
        {"min_score": 0, "max_score": 39.99, "code": "F", "remark": "Needs Support", "rank": 6},
    ]
    jhs_bands = [
        {"min_score": 85, "max_score": 100, "code": "1", "remark": "Highest", "rank": 1},
        {"min_score": 70, "max_score": 84.99, "code": "2", "remark": "Higher", "rank": 2},
        {"min_score": 55, "max_score": 69.99, "code": "3", "remark": "High", "rank": 3},
        {"min_score": 40, "max_score": 54.99, "code": "4", "remark": "Average", "rank": 4},
        {"min_score": 0, "max_score": 39.99, "code": "5", "remark": "Developing", "rank": 5},
    ]
    grading.create_scale(db, school_id=school.id, name="Primary scale",
                         bands_payload=primary_bands, scope_band="PRIMARY")
    grading.create_scale(db, school_id=school.id, name="JHS scale (school-configured)",
                         bands_payload=jhs_bands, scope_band="JHS")
    grading.create_scale(db, school_id=school.id, name="School default scale",
                         bands_payload=primary_bands, is_default=True)

    # --- assessment schemes: Primary 50/50, JHS 30/70 (config rows — REQ-ASM-01) ---
    grade_rows = db.scalars(select(GradeM).where(GradeM.school_id == school.id)).all()
    for g in grade_rows:
        if g.band == "EARLY_CHILDHOOD":
            continue  # ECD is qualitative (BR-M07)
        weights = (50, 50) if g.band == "PRIMARY" else (30, 70)
        assess.upsert_scheme(
            db, school_id=school.id, academic_year_id=year_cur.id, term_id=term1.id,
            grade_id=g.id, subject_id=None,
            components_payload=[
                {"code": "CLASS_SCORE",
                 "name": "Class Score" if g.band == "PRIMARY" else "Continuous Assessment",
                 "kind": "CLASS", "weight_pct": weights[0], "max_score": 100},
                {"code": "TERMINAL_EXAM", "name": "Terminal Examination",
                 "kind": "EXAM", "weight_pct": weights[1], "max_score": 100}])

    subjects = {s.code: s for s in db.scalars(
        select(Subject).where(Subject.school_id == school.id)).all()}
    current_streams = db.scalars(select(ClassStream).where(
        ClassStream.school_id == school.id,
        ClassStream.academic_year_id == year_cur.id)).all()
    stream_grade = {s.id: db.get(GradeM, s.grade_id) for s in current_streams}

    # --- marks for ENG & MAT on Primary/JHS streams ---
    seeded_sheets = 0
    for stream in current_streams:
        grade = stream_grade[stream.id]
        if grade.band == "EARLY_CHILDHOOD":
            continue
        enrollments = db.scalars(select(Enrollment).where(
            Enrollment.class_stream_id == stream.id,
            Enrollment.status == "ACTIVE")).all()
        if not enrollments:
            continue
        for subj_code in ("ENG", "MAT"):
            subj = subjects.get(subj_code)
            if subj is None:
                continue
            scheme = assess.resolve_scheme(db, school_id=school.id, term_id=term1.id,
                                           grade_id=grade.id, subject_id=subj.id)
            if scheme is None:
                continue
            for comp in assess.scheme_components(db, scheme.id):
                sheet = assess.get_or_create_sheet(
                    db, school_id=school.id, term_id=term1.id,
                    class_stream_id=stream.id, subject_id=subj.id,
                    component_id=comp.id)
                base = rng.randint(45, 75)
                entries = [{"enrollment_id": e.id,
                            "raw_score": min(float(comp.max_score),
                                             max(5.0, base + rng.randint(-20, 25)))}
                           for e in enrollments]
                assess.save_draft_scores(db, sheet, entries, actor_id=admin.id)
                seeded_sheets += 1
                if rng.random() < 0.6:  # most sheets submitted, some stay draft
                    assess.submit_sheet(db, sheet, actor_id=admin.id,
                                        allow_incomplete=True)

    # --- ECD developmental ratings + observations ---
    domains = ecd.domains(db, school.id)
    ratings_seed = 0
    for stream in current_streams:
        if stream_grade[stream.id].band != "EARLY_CHILDHOOD":
            continue
        for e in db.scalars(select(Enrollment).where(
                Enrollment.class_stream_id == stream.id,
                Enrollment.status == "ACTIVE")).all():
            for d in domains[:6]:
                ecd.upsert_rating(db, school_id=school.id, enrollment_id=e.id,
                                  term_id=term1.id, domain_id=d.id,
                                  rating=rng.choice(["EMERGING", "DEVELOPING", "ACHIEVED"]),
                                  comment=None, actor_id=admin.id)
                ratings_seed += 1
            if rng.random() < 0.3:
                ecd.add_observation(
                    db, school_id=school.id, enrollment_id=e.id,
                    logged_on=term1.starts_on + _td(days=rng.randint(1, 20)),
                    body=rng.choice([
                        "Settled well after break; joined group singing.",
                        "Improving at holding a pencil; drew shapes unprompted.",
                        "Shared toys during free play; very cooperative.",
                        "Counted blocks to ten with light prompting.",
                    ]),
                    author_id=admin.id)

    # --- core competency ratings (sample) ---
    comps = db.scalars(select(CoreCompetency).where(
        CoreCompetency.school_id == school.id)).all()
    for e in db.scalars(select(Enrollment).where(
            Enrollment.academic_year_id == year_cur.id,
            Enrollment.status == "ACTIVE").limit(120)).all():
        for c in comps[:4]:
            ecd.upsert_competency_rating(db, school_id=school.id, enrollment_id=e.id,
                                         term_id=term1.id, competency_id=c.id,
                                         rating=rng.choice(["EMERGING", "DEVELOPING",
                                                            "ACHIEVED"]),
                                         comment=None, actor_id=admin.id)

    # --- attendance: first 10 weekdays of the term, submitted sheets ---
    day = term1.starts_on
    taken = 0
    while taken < 10:
        if day.weekday() < 5:
            for stream in current_streams[: (12 if len(current_streams) > 12
                                             else len(current_streams))]:
                enrs = db.scalars(select(Enrollment).where(
                    Enrollment.class_stream_id == stream.id,
                    Enrollment.status == "ACTIVE")).all()
                if not enrs:
                    continue
                records = [{"enrollment_id": e.id,
                            "status": rng.choices(
                                ["PRESENT", "LATE", "ABSENT", "EXCUSED"],
                                weights=[88, 5, 4, 3])[0]} for e in enrs]
                sheet = att.upsert_sheet(db, school_id=school.id, stream_id=stream.id,
                                         term_id=term1.id, sheet_date=day,
                                         records=records, actor_id=admin.id)
                att.submit_sheet(db, sheet, actor_id=admin.id)
            taken += 1
        day += _td(days=1)

    # --- curriculum sample tree (B1 Mathematics, small NaCCA-shaped extract) ---
    cur = db.scalar(select(Curriculum).where(Curriculum.school_id == school.id))
    if cur is None:
        cur = Curriculum(id=uuid7(), school_id=school.id,
                         name="NaCCA Basic School Curriculum", origin="NATIONAL")
        db.add(cur)
        db.flush()
    version = curr.create_version(db, school_id=school.id, curriculum_id=cur.id,
                                  version_label="2026.v1", actor_id=admin.id)
    strand = curr.add_strand(db, school_id=school.id, version=version,
                             grade_id=grades["B1"].id, subject_id=subjects["MAT"].id,
                             code="S1", title="Numbers")
    db.flush()
    from app.models.academic import ContentStandard, SubStrand
    sub = SubStrand(id=uuid7(), school_id=school.id, strand_id=strand.id,
                    code="S1.1", title="Counting and representation", ordinal=1)
    db.add(sub)
    db.flush()
    cs = ContentStandard(id=uuid7(), school_id=school.id, sub_strand_id=sub.id,
                         code="S1.1.1", title="Count objects up to 100", ordinal=1)
    db.add(cs)
    db.flush()
    db.add(Indicator(id=uuid7(), school_id=school.id, content_standard_id=cs.id,
                     code="B1.1.1.1", title="Count forwards and backwards to 100",
                     ordinal=1))
    curr.publish_version(db, version, actor_id=admin.id)

    # --- published sample reports (2 per band) for the parent portal demo ---
    published = 0
    seen_bands = set()
    for stream in current_streams:
        band = stream_grade[stream.id].band
        if band in seen_bands:
            continue
        enrs = db.scalars(select(Enrollment).where(
            Enrollment.class_stream_id == stream.id,
            Enrollment.status == "ACTIVE").limit(2)).all()
        if not enrs:
            continue
        for e in enrs:
            try:
                report = reports.generate_report(
                    db, school=school, student_id=e.student_id, term_id=term1.id,
                    actor_id=admin.id,
                    teacher_remark="A pleasant and attentive learner.",
                    head_remark="Keep it up.")
                reports.finalize_report(db, report, actor_id=admin.id)
                reports.publish_report(db, report, actor_id=admin.id)
                published += 1
            except Exception as exc:  # demo convenience — never fail the seed
                print(f"[seed] report skipped: {exc}")
        seen_bands.add(band)

    print(f"[seed] academics: schemes for {len(grade_rows) - 5} grades, "
          f"{seeded_sheets} mark sheets, {ratings_seed} ECD ratings, "
          f"{published} published reports")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reset", action="store_true")
    ap.add_argument("--fast", action="store_true")
    args = ap.parse_args()

    settings = get_settings()
    if args.reset:
        engine = get_engine()
        with engine.begin() as conn:
            Base.metadata.drop_all(conn)
            Base.metadata.create_all(conn)
        print("[seed] schema recreated")

    Session = get_session_factory()
    db = Session()

    # ------------------------------------------------------------------ school
    school = db.scalar(select(School))
    if school is None:
        school = catalog.create_school(
            db, settings.default_school_name,
            short_name="HSA", motto="Knowledge • Discipline • Service",
            location="Accra, Greater Accra Region",
            ghana_digital_address="GA-123-4567", phone=rand_phone(),
            email="info@hopestar.demo")
        db.flush()
        print(f"[seed] school created: {school.name}")

    departments = catalog.bootstrap_departments(db, school.id)
    catalog.bootstrap_permissions(db)
    roles = catalog.bootstrap_roles(db, school.id)
    grades = catalog.bootstrap_grades(db, school.id, departments)
    catalog.bootstrap_subjects(db, school.id, grades)

    # ------------------------------------------------------------------ calendar
    def make_year(name: str, start: date) -> AcademicYear:
        y = db.scalar(select(AcademicYear).where(AcademicYear.name == name,
                                                 AcademicYear.school_id == school.id))
        if y is None:
            y = AcademicYear(id=uuid7(), school_id=school.id, name=name,
                             starts_on=start, ends_on=start.replace(year=start.year + 1) - timedelta(days=1))
            db.add(y)
            db.flush()
        return y

    year_prev = make_year("2025/2026", date(2025, 9, 8))
    year_cur = make_year("2026/2027", date(2026, 9, 7))
    year_prev.status = "ARCHIVED"
    year_cur.status = "ACTIVE"

    def make_terms(year: AcademicYear) -> list[Term]:
        terms = []
        spans = [("Term 1", 0, 90), ("Term 2", 100, 190), ("Term 3", 200, 280)]
        for name, s, e in spans:
            t = db.scalar(select(Term).where(Term.academic_year_id == year.id, Term.name == name))
            if t is None:
                t = Term(id=uuid7(), school_id=school.id, academic_year_id=year.id,
                         name=name, starts_on=year.starts_on + timedelta(days=s),
                         ends_on=year.starts_on + timedelta(days=e),
                         status="CLOSED" if year.id == year_prev.id else "DRAFT")
                db.add(t)
                db.flush()
            terms.append(t)
        return terms

    make_terms(year_prev)
    terms_cur = make_terms(year_cur)
    terms_cur[0].status = "ACTIVE"
    db.flush()

    # ------------------------------------------------------------------ users
    def make_user(username: str, display: str, role_code: str, **links) -> User:
        u = db.scalar(select(User).where(User.username == username))
        if u is None:
            u = User(id=uuid7(), username=username, display_name=display,
                     password_hash=security.hash_password(DEMO_PASSWORD, settings), **links)
            db.add(u)
            db.flush()
            db.add(UserRole(user_id=u.id, role_id=roles[role_code].id, granted_by=u.id))
            db.flush()
        return u

    admin = make_user("admin", "System Administrator", rbac.SUPER_ADMIN)
    make_user("head", "Dorothy head-of-school", rbac.HEAD_TEACHER)
    make_user("bursar", "Kwabena Bursar", rbac.BURSAR)
    db.flush()

    # ------------------------------------------------------------------ teachers & classes
    n_streams_per_grade = 2 if not args.fast else 1
    grade_list = list(catalog.GRADES)
    if args.fast:
        grade_list = [g for g in catalog.GRADES if g[0] in
                      ("KG1", "B1", "B4", "B6", "JHS1", "JHS3")]

    streams: dict[tuple[str, uuid.UUID], ClassStream] = {}
    for year in (year_prev, year_cur):
        for code, name, ordinal, band, _dept in grade_list:
            for i in range(n_streams_per_grade):
                label = chr(ord("A") + i)
                exists = db.scalar(select(ClassStream).where(
                    ClassStream.school_id == school.id,
                    ClassStream.grade_id == grades[code].id,
                    ClassStream.academic_year_id == year.id,
                    ClassStream.section_label == label))
                if exists is None:
                    exists = ClassStream(id=uuid7(), school_id=school.id,
                                         grade_id=grades[code].id,
                                         academic_year_id=year.id,
                                         name=f"{name} {label}", section_label=label,
                                         capacity=40)
                    db.add(exists)
                    db.flush()
                streams[(code, year.id)] = exists if i == 0 else streams.get((code, year.id), exists)
                streams[(f"{code}#{label}", year.id)] = exists

    n_teachers = 8 if args.fast else 30
    teachers: list[Teacher] = []
    for i in range(n_teachers):
        surname = rng.choice(STAFF_SURNAMES)
        other = rng.choice(OTHER_NAMES_F + OTHER_NAMES_M)
        t = db.scalar(select(Teacher).where(Teacher.school_id == school.id,
                                            Teacher.surname == surname,
                                            Teacher.other_names == other))
        if t is None:
            t = Teacher(id=uuid7(), school_id=school.id, staff_code=f"HSA-T{i+1:03d}",
                        surname=surname, other_names=other,
                        gender=rng.choice(["F", "M"]), phone=rand_phone(),
                        email=f"teacher{i+1}@hopestar.demo", job_title="Teacher",
                        qualification=rng.choice(["Diploma in Basic Education",
                                                  "B.Ed Mathematics", "B.Ed Early Childhood",
                                                  "B.Ed English"]),
                        hired_on=date(rng.randint(2015, 2024), rng.randint(1, 12), rng.randint(1, 28)))
            db.add(t)
            db.flush()
            if i < 6 or not args.fast:
                tu = make_user(f"teacher{i+1}", f"{other} {surname}", rbac.TEACHER,
                               teacher_id=t.id)
        teachers.append(t)
    db.flush()

    # teacher assignments: spread teachers across current-year streams
    current_streams = [s for (code, yid), s in streams.items()
                       if yid == year_cur.id and "#" not in code]
    for idx, stream in enumerate(current_streams):
        teacher = teachers[idx % len(teachers)]
        exists = db.scalar(select(TeacherAssignment).where(
            TeacherAssignment.teacher_id == teacher.id,
            TeacherAssignment.class_stream_id == stream.id,
            TeacherAssignment.role == "FORM_TEACHER"))
        if exists is None:
            db.add(TeacherAssignment(id=uuid7(), school_id=school.id, teacher_id=teacher.id,
                                     academic_year_id=year_cur.id, class_stream_id=stream.id,
                                     role="FORM_TEACHER"))
    db.flush()

    # ------------------------------------------------------------------ students & guardians
    n_students = 60 if args.fast else 720
    students: list[Student] = []
    guardians: list[ParentGuardian] = []

    existing_students = db.scalar(select(Student.id).where(Student.school_id == school.id).limit(1))
    if existing_students is None:
        for i in range(n_students):
            grade_code, _g_name, ordinal, band, _d = rng.choice(grade_list)
            gender = rng.choice(["F", "M"])
            surname = rng.choice(SURNAMES)
            other = rng.choice(OTHER_NAMES_F if gender == "F" else OTHER_NAMES_M)
            age = ordinal + rng.randint(4, 6)
            dob = date(2026 - age, rng.randint(1, 12), rng.randint(1, 28))
            s = Student(id=uuid7(), school_id=school.id,
                        admission_code=f"HSA-{i+1:04d}", surname=surname,
                        other_names=other, gender=gender, date_of_birth=dob,
                        status="ACTIVE", admitted_on=year_prev.starts_on)
            db.add(s)
            students.append(s)
        db.flush()
        print(f"[seed] {len(students)} students created")
        # advance the admission-code sequence past the manually coded students
        from app.models.core import DocumentSequence
        seq = db.scalar(select(DocumentSequence).where(
            DocumentSequence.school_id == school.id,
            DocumentSequence.key == "ADMISSION_CODE"))
        if seq is None:
            db.add(DocumentSequence(id=uuid7(), school_id=school.id, key="ADMISSION_CODE",
                                    prefix="HSA", current_value=len(students)))
        else:
            seq.current_value = max(seq.current_value, len(students))
        db.flush()

        # guardians: ~65% of students share family groups → siblings & multi-child parents
        family_idx = 0
        per_family = {}
        for s in students:
            family_idx = rng.random()
            if rng.random() < 0.35 and per_family:
                fam = rng.choice(list(per_family))
                per_family[fam].append(s)
            else:
                per_family.setdefault(s, []).append(s)

        for fam_key, kids in per_family.items():
            g = ParentGuardian(id=uuid7(), school_id=school.id,
                               name=f"{rng.choice(OTHER_NAMES_F + OTHER_NAMES_M)} {fam_key.surname}",
                               phone=rand_phone(),
                               email=f"parent{len(guardians)+1}@hopestar.demo" if rng.random() < 0.5 else None,
                               occupation=rng.choice(["Trader", "Nurse", "Driver", "Teacher",
                                                      "Farmer", "Seamstress", "Accountant", None]),
                               residential_address=fake.address().replace("\n", ", "),
                               ghana_digital_address=f"GA-{rng.randint(100, 999)}-{rng.randint(1000, 9999)}",
                               sms_opt_out=rng.random() < 0.05)
            db.add(g)
            guardians.append(g)
            for k_idx, kid in enumerate(kids):
                db.add(ParentStudentRelationship(
                    id=uuid7(), school_id=school.id, parent_id=g.id, student_id=kid.id,
                    relationship_type=rng.choice(["MOTHER", "FATHER", "GUARDIAN"]),
                    is_primary_contact=(k_idx == 0), is_billing_contact=(k_idx == 0),
                    source="MANUAL"))
        db.flush()
        print(f"[seed] {len(guardians)} guardians created (multi-child families included)")

        # enrollments: distribute students across current-year streams round-robin
        for idx, s in enumerate(students):
            stream = current_streams[idx % len(current_streams)]
            db.add(Enrollment(id=uuid7(), school_id=school.id, student_id=s.id,
                              academic_year_id=year_cur.id, class_stream_id=stream.id,
                              status="ACTIVE", started_on=year_cur.starts_on))
        db.flush()
        print(f"[seed] {len(students)} enrollments created for {year_cur.name}")
    else:
        print("[seed] students already present — skipping people stage")

    # parent logins for first two guardians
    for gi, g in enumerate(guardians[:2]):
        uname = f"parent{gi+1}"
        if db.scalar(select(User).where(User.username == uname)) is None:
            pu = User(id=uuid7(), username=uname, display_name=g.name, parent_id=g.id,
                      password_hash=security.hash_password(DEMO_PASSWORD, settings))
            db.add(pu)
            db.flush()
            db.add(UserRole(user_id=pu.id, role_id=roles[rbac.PARENT].id, granted_by=admin.id))
    db.flush()

    seed_academics(db, school, roles, grades, year_cur, terms_cur, streams, students,
                   teachers, admin, settings)

    seed_finance(db, school, grades, year_cur, terms_cur, admin)

    seed_operations(db, school, year_cur, terms_cur, teachers, students, admin)

    db.commit()

    print("\n=== DEMO CREDENTIALS (fictional data — password for all) ===")
    print(f"  password: {DEMO_PASSWORD}")
    for uname in ("admin", "head", "bursar", "teacher1", "teacher2", "parent1", "parent2"):
        print(f"  - {uname}")
    print("============================================================\n")


if __name__ == "__main__":
    main()
