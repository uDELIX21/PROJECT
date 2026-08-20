"""Pydantic request models (strict validation — REQ-API-02)."""
import uuid
from datetime import date
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

Gender = Literal["F", "M"]
RelationshipType = Literal["MOTHER", "FATHER", "GUARDIAN", "GRANDPARENT", "SIBLING", "OTHER"]
AssignmentRole = Literal["SUBJECT_TEACHER", "FORM_TEACHER"]
PromotionDecision = Literal["PROMOTE", "REPEAT", "WITHDRAW", "TRANSFER", "GRADUATE"]
StudentStatusAction = Literal["ADMITTED", "ACTIVE", "SUSPENDED", "WITHDRAWN", "TRANSFERRED",
                              "GRADUATED", "APPLICANT"]


class LoginIn(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=256)


class PasswordChangeIn(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=10, max_length=256)


class PasswordResetRequestIn(BaseModel):
    username: str = Field(min_length=1, max_length=64)


class PasswordResetConfirmIn(BaseModel):
    token: str = Field(min_length=16, max_length=128)
    new_password: str = Field(min_length=10, max_length=256)


class StudentCreateIn(BaseModel):
    surname: str = Field(min_length=1, max_length=80)
    other_names: str = Field(min_length=1, max_length=160)
    gender: Gender
    date_of_birth: date
    admit: bool = False

    @field_validator("surname", "other_names")
    @classmethod
    def _strip_nonempty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("must not be blank")
        return v


class StudentPatchIn(BaseModel):
    surname: str | None = Field(default=None, min_length=1, max_length=80)
    other_names: str | None = Field(default=None, min_length=1, max_length=160)
    gender: Gender | None = None
    date_of_birth: date | None = None
    nationality: str | None = Field(default=None, max_length=48)
    religion: str | None = Field(default=None, max_length=48)
    medical_notes: str | None = Field(default=None, max_length=4000)


class StudentStatusIn(BaseModel):
    status: StudentStatusAction
    reason: str | None = Field(default=None, max_length=500)


class GuardianCreateIn(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    phone: str = Field(min_length=5, max_length=24)
    phone2: str | None = Field(default=None, max_length=24)
    email: EmailStr | None = None
    occupation: str | None = Field(default=None, max_length=120)
    residential_address: str | None = Field(default=None, max_length=1000)
    ghana_digital_address: str | None = Field(default=None, max_length=40)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    sms_opt_out: bool = False


class GuardianLinkIn(BaseModel):
    student_id: uuid.UUID
    relationship_type: RelationshipType
    is_primary_contact: bool = False
    is_billing_contact: bool = False


class TeacherCreateIn(BaseModel):
    surname: str = Field(min_length=1, max_length=80)
    other_names: str = Field(min_length=1, max_length=160)
    gender: Gender | None = None
    phone: str | None = Field(default=None, max_length=24)
    email: EmailStr | None = None
    qualification: str | None = Field(default=None, max_length=160)
    job_title: str | None = Field(default=None, max_length=80)
    hired_on: date | None = None


class AssignmentCreateIn(BaseModel):
    teacher_id: uuid.UUID
    academic_year_id: uuid.UUID
    class_stream_id: uuid.UUID
    subject_id: uuid.UUID | None = None
    role: AssignmentRole = "SUBJECT_TEACHER"


class YearCreateIn(BaseModel):
    name: str = Field(min_length=3, max_length=16)
    starts_on: date
    ends_on: date


class TermCreateIn(BaseModel):
    name: str = Field(min_length=2, max_length=24)
    starts_on: date
    ends_on: date


class TermReopenIn(BaseModel):
    reason: str = Field(min_length=5, max_length=500)


class StreamCreateIn(BaseModel):
    grade_id: uuid.UUID
    academic_year_id: uuid.UUID
    section_label: str = Field(min_length=1, max_length=8)
    name: str | None = Field(default=None, max_length=60)
    capacity: int | None = Field(default=None, gt=0)


class GradeCreateIn(BaseModel):
    code: str = Field(min_length=1, max_length=16)
    name: str = Field(min_length=1, max_length=60)
    ordinal: int = Field(gt=0)
    band: Literal["EARLY_CHILDHOOD", "PRIMARY", "JHS"]


class SubjectCreateIn(BaseModel):
    code: str = Field(min_length=1, max_length=24)
    name: str = Field(min_length=1, max_length=80)


class EnrollmentCreateIn(BaseModel):
    student_id: uuid.UUID
    class_stream_id: uuid.UUID
    academic_year_id: uuid.UUID | None = None
    is_repeat: bool = False


class PromotionApplyIn(BaseModel):
    from_academic_year_id: uuid.UUID
    to_academic_year_id: uuid.UUID
    stream_mapping: dict[str, str] = {}  # grade_id -> target stream_id
    decisions: list[dict] = []  # [{student_id, decision, to_class_stream_id?, note?}]


class UserCreateIn(BaseModel):
    username: str = Field(min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9._-]+$")
    password: str = Field(min_length=10, max_length=256)
    display_name: str | None = Field(default=None, max_length=160)
    email: EmailStr | None = None
    role_codes: list[str] = []
    teacher_id: uuid.UUID | None = None
    parent_id: uuid.UUID | None = None
    student_id: uuid.UUID | None = None


class UserPatchIn(BaseModel):
    status: Literal["ACTIVE", "LOCKED", "DEACTIVATED"] | None = None
    display_name: str | None = Field(default=None, max_length=160)
    email: EmailStr | None = None


class RoleGrantIn(BaseModel):
    role_code: str
    reason: str | None = Field(default=None, max_length=500)


class SchoolPatchIn(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    short_name: str | None = Field(default=None, max_length=40)
    motto: str | None = Field(default=None, max_length=255)
    location: str | None = Field(default=None, max_length=255)
    ghana_digital_address: str | None = Field(default=None, max_length=40)
    phone: str | None = Field(default=None, max_length=20)
    email: EmailStr | None = None


# --------------------------------------------------------------------------- Phase 4

class SchemeComponentIn(BaseModel):
    code: str = Field(min_length=1, max_length=32)
    name: str | None = Field(default=None, max_length=80)
    kind: Literal["CLASS", "EXAM"] = "CLASS"
    weight_pct: float = Field(gt=0, le=100)
    max_score: float = Field(default=100, gt=0)
    aggregation: Literal["DIRECT", "MEAN", "BEST"] = "DIRECT"


class SchemeUpsertIn(BaseModel):
    academic_year_id: uuid.UUID
    term_id: uuid.UUID
    grade_id: uuid.UUID
    subject_id: uuid.UUID | None = None
    name: str = Field(default="Standard scheme", max_length=80)
    components: list[SchemeComponentIn] = Field(min_length=1)


class ScoreEntryIn(BaseModel):
    enrollment_id: uuid.UUID
    raw_score: float | None = Field(default=None, ge=0)
    is_absent: bool = False
    note: str | None = Field(default=None, max_length=255)


class ScoresSaveIn(BaseModel):
    sheet_id: uuid.UUID
    entries: list[ScoreEntryIn]


class SheetRefIn(BaseModel):
    sheet_id: uuid.UUID
    allow_incomplete: bool = False


class SheetSubmitIn(BaseModel):
    sheet_id: uuid.UUID
    allow_incomplete: bool = False


class CorrectionRequestIn(BaseModel):
    assessment_score_id: uuid.UUID
    new_score: float | None = Field(default=None, ge=0)
    reason: str = Field(min_length=5, max_length=1000)


class CorrectionResolveIn(BaseModel):
    approve: bool


class AttendanceRecordIn(BaseModel):
    enrollment_id: uuid.UUID
    status: Literal["PRESENT", "ABSENT", "LATE", "EXCUSED", "LEFT_EARLY"]
    note: str | None = Field(default=None, max_length=255)


class AttendanceSheetIn(BaseModel):
    class_stream_id: uuid.UUID
    term_id: uuid.UUID
    sheet_date: date
    records: list[AttendanceRecordIn]


class SheetSubmitRefIn(BaseModel):
    sheet_id: uuid.UUID


class RatingItemIn(BaseModel):
    domain_id: uuid.UUID
    rating: Literal["EMERGING", "DEVELOPING", "ACHIEVED"]
    comment: str | None = Field(default=None, max_length=1000)


class RatingsPutIn(BaseModel):
    enrollment_id: uuid.UUID
    term_id: uuid.UUID
    ratings: list[RatingItemIn] = Field(min_length=1)


class ObservationIn(BaseModel):
    enrollment_id: uuid.UUID
    logged_on: date | None = None
    body: str = Field(min_length=1, max_length=4000)
    supersedes: uuid.UUID | None = None


class CompetencyRatingItemIn(BaseModel):
    competency_id: uuid.UUID
    rating: Literal["EMERGING", "DEVELOPING", "ACHIEVED"]
    comment: str | None = Field(default=None, max_length=1000)


class CompetencyRatingIn(BaseModel):
    enrollment_id: uuid.UUID
    term_id: uuid.UUID
    ratings: list[CompetencyRatingItemIn] = Field(min_length=1)


class CurriculumCreateIn(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    origin: Literal["NATIONAL", "SCHOOL"] = "NATIONAL"
    description: str | None = Field(default=None, max_length=2000)


class VersionCreateIn(BaseModel):
    curriculum_id: uuid.UUID
    version_label: str = Field(min_length=1, max_length=32)
    copy_from_version_id: uuid.UUID | None = None


class StrandNodeIn(BaseModel):
    grade_id: uuid.UUID | None = None
    subject_id: uuid.UUID | None = None
    code: str = Field(min_length=1, max_length=32)
    title: str = Field(min_length=1, max_length=1000)
    ordinal: int = 1


class ScaleBandIn(BaseModel):
    min_score: float = Field(ge=0, le=100)
    max_score: float = Field(ge=0, le=100)
    code: str = Field(min_length=1, max_length=8)
    remark: str = Field(min_length=1, max_length=80)
    rank: int = Field(ge=1)


class ScaleCreateIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    scope_band: Literal["EARLY_CHILDHOOD", "PRIMARY", "JHS"] | None = None
    grade_id: uuid.UUID | None = None
    academic_year_id: uuid.UUID | None = None
    is_default: bool = False
    bands: list[ScaleBandIn] = Field(min_length=1)


class ScaleBandsPutIn(BaseModel):
    bands: list[ScaleBandIn] = Field(min_length=1)


class ReportGenerateIn(BaseModel):
    student_id: uuid.UUID
    term_id: uuid.UUID
    teacher_remark: str | None = Field(default=None, max_length=1000)
    head_remark: str | None = Field(default=None, max_length=1000)


class ReportPublishIn(BaseModel):
    override_reason: str | None = Field(default=None, max_length=500)


class TemplatePutIn(BaseModel):
    name: str | None = Field(default=None, max_length=80)
    layout_config: dict | None = None


# --------------------------------------------------------------------------- Phase 5

class FeeItemIn(BaseModel):
    fee_type: Literal["TUITION", "FEEDING", "ICT_LAB", "PTA_LEVY", "TRANSPORT",
                      "EXAMINATION", "OTHER"]
    display_name: str | None = Field(default=None, max_length=80)
    amount_pesewas: int = Field(ge=0)
    period: Literal["PER_TERM", "PER_YEAR", "ONE_OFF"] = "PER_TERM"
    term_id: uuid.UUID | None = None


class StructureCreateIn(BaseModel):
    academic_year_id: uuid.UUID
    name: str = Field(min_length=1, max_length=80)
    grade_id: uuid.UUID | None = None
    band: Literal["EARLY_CHILDHOOD", "PRIMARY", "JHS"] | None = None
    items: list[FeeItemIn] = Field(min_length=1)


class BillingRunIn(BaseModel):
    academic_year_id: uuid.UUID
    term_id: uuid.UUID


class ManualChargeIn(BaseModel):
    enrollment_id: uuid.UUID
    fee_type: Literal["TUITION", "FEEDING", "ICT_LAB", "PTA_LEVY", "TRANSPORT",
                      "EXAMINATION", "OTHER"]
    display_name: str = Field(min_length=1, max_length=80)
    amount_pesewas: int = Field(gt=0)
    term_id: uuid.UUID | None = None


class WaiverIn(BaseModel):
    enrollment_id: uuid.UUID
    kind: Literal["WAIVER", "DISCOUNT", "SCHOLARSHIP"]
    amount_pesewas: int | None = Field(default=None, gt=0)
    pct: float | None = Field(default=None, gt=0, le=100)
    reason: str = Field(min_length=5, max_length=1000)
    term_id: uuid.UUID | None = None
    fee_charge_id: uuid.UUID | None = None


class AdjustmentIn(BaseModel):
    enrollment_id: uuid.UUID
    direction: Literal["DEBIT", "CREDIT"]
    amount_pesewas: int = Field(gt=0)
    reason: str = Field(min_length=5, max_length=1000)
    term_id: uuid.UUID | None = None


class InstallmentIn(BaseModel):
    due_on: date
    amount_pesewas: int = Field(gt=0)


class PaymentPlanIn(BaseModel):
    enrollment_id: uuid.UUID
    term_id: uuid.UUID
    installments: list[InstallmentIn] = Field(min_length=1)
    note: str | None = Field(default=None, max_length=1000)


class PaymentInitiateIn(BaseModel):
    student_id: uuid.UUID
    amount_pesewas: int = Field(gt=0)
    method: Literal["MTN_MOMO", "TELECEL_CASH", "AT_MONEY", "CASH", "BANK_TRANSFER", "OTHER"]
    term_id: uuid.UUID | None = None
    payer_name: str | None = Field(default=None, max_length=160)
    payer_phone: str | None = Field(default=None, max_length=20)


class PaymentReverseIn(BaseModel):
    reason: str = Field(min_length=5, max_length=500)


class RefundIn(BaseModel):
    amount_pesewas: int = Field(gt=0)
    reason: str = Field(min_length=5, max_length=500)


class ReceiptVoidIn(BaseModel):
    reason: str = Field(min_length=5, max_length=500)


class ClearancePolicyIn(BaseModel):
    academic_year_id: uuid.UUID
    term_id: uuid.UUID | None = None
    clearance_type: Literal["REPORT_CARD", "EXAMINATION"]
    mode: Literal["PERCENT_OF_CHARGES", "FIXED_AMOUNT"]
    threshold: int = Field(ge=0)  # percent in basis points (100% = 10000) or pesewas
    band: Literal["EARLY_CHILDHOOD", "PRIMARY", "JHS"] | None = None
    grade_id: uuid.UUID | None = None


class ClearanceOverrideIn(BaseModel):
    student_id: uuid.UUID
    term_id: uuid.UUID
    clearance_type: Literal["REPORT_CARD", "EXAMINATION"] = "REPORT_CARD"
    state: Literal["WAIVED", "MANUAL_OVERRIDE", "PAYMENT_PLAN"]
    reason: str = Field(min_length=5, max_length=500)


# --------------------------------------------------------------------------- Phase 6

class AppraisalCreateIn(BaseModel):
    teacher_id: uuid.UUID
    period_from: date
    period_to: date


class AppraisalScoreItemIn(BaseModel):
    criterion_id: uuid.UUID
    score: float = Field(ge=0)
    comment: str | None = Field(default=None, max_length=2000)


class AppraisalScoresIn(BaseModel):
    scores: list[AppraisalScoreItemIn] = Field(min_length=1)


class AppraisalSubmitIn(BaseModel):
    overall_comment: str | None = Field(default=None, max_length=2000)


class CriterionIn(BaseModel):
    criterion_id: uuid.UUID
    max_score: int | None = Field(default=None, gt=0)
    weight_pct: float | None = Field(default=None, ge=0)
    is_active: bool | None = None


class IncidentCreateIn(BaseModel):
    student_id: uuid.UUID
    category: Literal["DISRUPTION", "BULLYING", "FIGHTING", "TRUANCY",
                      "DAMAGE_TO_PROPERTY", "DISRESPECT", "UNIFORM_VIOLATION",
                      "ACADEMIC_DISHONESTY", "OTHER"]
    description: str = Field(min_length=5, max_length=4000)
    severity: Literal["MINOR", "MODERATE", "SERIOUS"] = "MINOR"
    action_taken: str | None = Field(default=None, max_length=2000)


class IncidentUpdateIn(BaseModel):
    status: Literal["OPEN", "UNDER_REVIEW", "RESOLVED"]
    resolution: str | None = Field(default=None, max_length=2000)
    action_taken: str | None = Field(default=None, max_length=2000)


class PickupCreateIn(BaseModel):
    student_id: uuid.UUID
    person_name: str = Field(min_length=1, max_length=160)
    relationship: str | None = Field(default=None, max_length=80)
    phone: str | None = Field(default=None, max_length=20)
    id_reference: str | None = Field(default=None, max_length=80)
    expires_on: date | None = None


class PickupRevokeIn(BaseModel):
    reason: str = Field(min_length=5, max_length=500)


class BroadcastIn(BaseModel):
    event_code: Literal["PAYMENT_CONFIRMED", "FEE_REMINDER", "REPORT_AVAILABLE",
                        "EMERGENCY_BROADCAST", "ANNOUNCEMENT", "DISCIPLINE_NOTICE"]
    audience: Literal["school", "ecd", "primary", "jhs", "class", "debtors"]
    message: str | None = Field(default=None, max_length=1000)
    class_stream_id: uuid.UUID | None = None
    extra_vars: dict | None = None


class CommTemplatePutIn(BaseModel):
    template: str | None = Field(default=None, max_length=2000)
    is_active: bool | None = None


# --------------------------------------------------------------------------- Phase 7

class SyncMutationIn(BaseModel):
    client_mutation_id: uuid.UUID
    # free string: unknown types get a structured MUTATION_TYPE_UNKNOWN verdict
    # from the service (robust to client/server version drift)
    entity_type: str = Field(max_length=32)
    entity_ref: str = Field(default="", max_length=160)
    base_version: int | None = None
    payload: dict


class SyncBatchIn(BaseModel):
    mutations: list[SyncMutationIn] = Field(min_length=1, max_length=100)


# --------------------------------------------------------------------------- Phase 8

class MatchResolveIn(BaseModel):
    action: Literal["LINK", "NEW", "SKIP"]
    guardian_id: uuid.UUID | None = None
