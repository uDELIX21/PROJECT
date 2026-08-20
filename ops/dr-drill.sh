#!/usr/bin/env bash
# Quarterly DR drill (spec §37: periodic restoration testing).
#
#   ops/dr-drill.sh [--dir /var/backups/sms]
#
# Restores the latest backup into a SCRATCH database, runs integrity checks,
# and reports PASS/FAIL. Safe to run against production backups: it never
# touches the live database.
set -euo pipefail

BACKUP_DIR="${1:-/var/backups/sms}"
SCRATCH_DB="${SCRATCH_DB:-postgresql://sms_app@localhost:5432/sms_drill}"

LATEST="$(ls -1t "${BACKUP_DIR}"/daily/sms-*.dump 2>/dev/null | head -1 || true)"
[[ -n "${LATEST}" ]] || { echo "[drill] FAIL: no daily backup found in ${BACKUP_DIR}/daily"; exit 1; }
echo "[drill] latest backup: ${LATEST}"

psql "${SCRATCH_DB}" -c "DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;" 2>/dev/null \
  || { echo "[drill] FAIL: cannot reach scratch DB ${SCRATCH_DB}"; exit 1; }

pg_restore -d "${SCRATCH_DB}" --no-owner --no-privileges "${LATEST}" || {
  echo "[drill] FAIL: pg_restore failed"; exit 1; }

# integrity checks
check() {
  local q="$1" desc="$2"
  local n
  n="$(psql "${SCRATCH_DB}" -Atc "${q}")"
  if [[ "${n}" -gt 0 ]]; then
    echo "[drill] ok: ${desc} = ${n}"
  else
    echo "[drill] FAIL: ${desc} empty"; exit 1
  fi
}
check "SELECT count(*) FROM students" "students"
check "SELECT count(*) FROM enrollments" "enrollments"
check "SELECT count(*) FROM ledger_entries" "ledger entries"
check "SELECT count(*) FROM audit_log" "audit rows"

# ledger balance identity spot-check (Σ debit − Σ credit per student)
BAD="$(psql "${SCRATCH_DB}" -Atc "
  SELECT count(*) FROM (
    SELECT student_id FROM ledger_entries GROUP BY student_id
    HAVING sum(CASE WHEN entry_type='DEBIT' THEN amount_pesewas ELSE 0 END)
         - sum(CASE WHEN entry_type='CREDIT' THEN amount_pesewas ELSE 0 END) < 0
  ) t;")"
echo "[drill] students with negative balance: ${BAD} (expected for overpayments/refunds)"

echo "[drill] PASS — restored ${LATEST} into scratch DB successfully"
psql "${SCRATCH_DB}" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" || true
