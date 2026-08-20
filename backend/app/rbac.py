"""Permission catalog & initial role matrix (design §06).

The catalog is fixed in code (authorization checks reference these constants);
the role→permission mapping is seeded into the DB and admin-editable later.
"""

# --- permission codes (REQ-RBAC-02) ---
VIEW_STUDENT = "VIEW_STUDENT"
EDIT_STUDENT = "EDIT_STUDENT"
VIEW_PARENT = "VIEW_PARENT"
EDIT_PARENT = "EDIT_PARENT"
VIEW_TEACHER = "VIEW_TEACHER"
EDIT_TEACHER = "EDIT_TEACHER"
MANAGE_ASSIGNMENTS = "MANAGE_ASSIGNMENTS"
MANAGE_CLASSES = "MANAGE_CLASSES"
MANAGE_ENROLLMENT = "MANAGE_ENROLLMENT"
MANAGE_CURRICULUM = "MANAGE_CURRICULUM"
ENTER_MARKS = "ENTER_MARKS"
SUBMIT_MARKS = "SUBMIT_MARKS"
OVERRIDE_MARKS = "OVERRIDE_MARKS"
MANAGE_ATTENDANCE = "MANAGE_ATTENDANCE"
VIEW_REPORT = "VIEW_REPORT"
MANAGE_REPORTS = "MANAGE_REPORTS"
VIEW_GRADES_CONFIG = "VIEW_GRADES_CONFIG"
MANAGE_GRADES_CONFIG = "MANAGE_GRADES_CONFIG"
VIEW_FINANCE = "VIEW_FINANCE"
MANAGE_FEES = "MANAGE_FEES"
CREATE_PAYMENT = "CREATE_PAYMENT"
VOID_PAYMENT = "VOID_PAYMENT"
GRANT_WAIVER = "GRANT_WAIVER"
MANAGE_CLEARANCE = "MANAGE_CLEARANCE"
IMPORT_DATA = "IMPORT_DATA"
SEND_COMMUNICATION = "SEND_COMMUNICATION"
APPRAISE_TEACHER = "APPRAISE_TEACHER"
VIEW_DISCIPLINE = "VIEW_DISCIPLINE"
MANAGE_DISCIPLINE = "MANAGE_DISCIPLINE"
MANAGE_PICKUP = "MANAGE_PICKUP"
MANAGE_USERS = "MANAGE_USERS"
MANAGE_SETTINGS = "MANAGE_SETTINGS"
VIEW_AUDIT = "VIEW_AUDIT"

PERMISSIONS: dict[str, tuple[str, str]] = {
    VIEW_STUDENT: ("View students", "Read student registry data"),
    EDIT_STUDENT: ("Edit students", "Create/update student records"),
    VIEW_PARENT: ("View parents/guardians", "Read guardian registry data"),
    EDIT_PARENT: ("Edit parents/guardians", "Create/update guardian records & links"),
    VIEW_TEACHER: ("View teachers", "Read teacher registry data"),
    EDIT_TEACHER: ("Edit teachers", "Create/update teacher records"),
    MANAGE_ASSIGNMENTS: ("Manage assignments", "Teacher↔class/subject assignments"),
    MANAGE_CLASSES: ("Manage classes", "Grades, streams, rosters"),
    MANAGE_ENROLLMENT: ("Manage enrollment", "Enroll, withdraw, promotion batches"),
    MANAGE_CURRICULUM: ("Manage curriculum", "Curriculum versions & tree"),
    ENTER_MARKS: ("Enter marks", "Draft scores & attendance (assignment-scoped)"),
    SUBMIT_MARKS: ("Submit marks", "Submit mark sheets"),
    OVERRIDE_MARKS: ("Override marks", "Approve score corrections / unlock sheets"),
    MANAGE_ATTENDANCE: ("Manage attendance", "Attendance config & cross-class summaries"),
    VIEW_REPORT: ("View reports", "Report card viewing"),
    MANAGE_REPORTS: ("Manage reports", "Generate/finalize/publish reports & templates"),
    VIEW_GRADES_CONFIG: ("View grading config", "Read grading scales & schemes"),
    MANAGE_GRADES_CONFIG: ("Manage grading config", "Edit grading scales & schemes"),
    VIEW_FINANCE: ("View finance", "Charges, balances, ledger, receipts"),
    MANAGE_FEES: ("Manage fees", "Fee structures, billing runs, plans"),
    CREATE_PAYMENT: ("Create payment", "Initiate/record payments"),
    VOID_PAYMENT: ("Void payment", "Reverse/refund payments, void receipts"),
    GRANT_WAIVER: ("Grant waiver", "Waivers, discounts, scholarships, adjustments"),
    MANAGE_CLEARANCE: ("Manage clearance", "Clearance policies & overrides"),
    IMPORT_DATA: ("Import data", "Bulk CSV/XLSX imports"),
    SEND_COMMUNICATION: ("Send communication", "Broadcasts & SMS"),
    APPRAISE_TEACHER: ("Appraise teacher", "Create/submit appraisals"),
    VIEW_DISCIPLINE: ("View discipline", "Read discipline incidents"),
    MANAGE_DISCIPLINE: ("Manage discipline", "Create/resolve discipline incidents"),
    MANAGE_PICKUP: ("Manage pickup", "Pickup authorizations"),
    MANAGE_USERS: ("Manage users", "User accounts & role grants"),
    MANAGE_SETTINGS: ("Manage settings", "School settings, terms open/close"),
    VIEW_AUDIT: ("View audit", "Audit log access"),
}

# --- roles ---
SUPER_ADMIN = "SUPER_ADMIN"
HEAD_TEACHER = "HEAD_TEACHER"
BURSAR = "BURSAR"
TEACHER = "TEACHER"
PARENT = "PARENT"
STUDENT = "STUDENT"

ROLE_NAMES = {
    SUPER_ADMIN: "Super Admin",
    HEAD_TEACHER: "Headmaster/Headteacher",
    BURSAR: "Bursar",
    TEACHER: "Teacher",
    PARENT: "Parent",
    STUDENT: "Student",
}

_ALL = set(PERMISSIONS)

# Initial role → permission matrix (design §06 table 4).
ROLE_MATRIX: dict[str, set[str]] = {
    SUPER_ADMIN: set(_ALL),
    HEAD_TEACHER: _ALL - {MANAGE_USERS},  # head manages non-admin accounts via scoped UI
    BURSAR: {
        VIEW_STUDENT, VIEW_FINANCE, MANAGE_FEES, CREATE_PAYMENT, MANAGE_CLEARANCE,
        SEND_COMMUNICATION, VIEW_REPORT, VIEW_AUDIT,
    },
    TEACHER: {
        VIEW_STUDENT, VIEW_PARENT, VIEW_TEACHER, VIEW_REPORT, VIEW_GRADES_CONFIG,
        ENTER_MARKS, SUBMIT_MARKS, MANAGE_ATTENDANCE, SEND_COMMUNICATION,
        VIEW_DISCIPLINE, MANAGE_DISCIPLINE,
        # curriculum is read-only for teachers (via VIEW_GRADES_CONFIG);
        # MANAGE_CURRICULUM stays with head/admin (design §06 matrix)
    },
    # VIEW_DISCIPLINE for parents is route-scoped: resolved summaries of their
    # own children only (design §28 confidentiality)
    PARENT: {VIEW_STUDENT, VIEW_REPORT, VIEW_FINANCE, VIEW_DISCIPLINE},
    STUDENT: {VIEW_STUDENT, VIEW_REPORT, VIEW_FINANCE},
}
