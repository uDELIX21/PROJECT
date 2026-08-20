#!/usr/bin/env bash
# SMS database restore (design §13 / spec §37).
#
#   ops/restore.sh <dump-file> [--target-db postgresql://user:pass@host:5432/db] [--yes]
#
# Restores a custom-format dump produced by ops/backup.sh into the target
# database. The target schema is DROPPED and recreated — never point this at
# a database you care about without --yes.
set -euo pipefail

DUMP="${1:?usage: ops/restore.sh <dump-file> [--target-db URL] [--yes]}"
TARGET_DB="${DATABASE_URL:?set DATABASE_URL or pass --target-db}"
CONFIRMED=0

shift
while [[ $# -gt 0 ]]; do
  case "$1" in
    --target-db) TARGET_DB="$2"; shift 2 ;;
    --yes) CONFIRMED=1; shift ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

[[ -f "${DUMP}" ]] || { echo "dump not found: ${DUMP}" >&2; exit 1; }

# verify checksum when present
if [[ -f "${DUMP}.sha256" ]]; then
  ( cd "$(dirname "${DUMP}")" && sha256sum -c "$(basename "${DUMP}").sha256" )
fi

if [[ "${CONFIRMED}" != "1" ]]; then
  echo "About to DESTROY and restore: ${TARGET_DB}"
  read -r -p "Type RESTORE to continue: " ans
  [[ "${ans}" == "RESTORE" ]] || { echo "aborted"; exit 1; }
fi

echo "[restore] dropping existing schema"
psql "${TARGET_DB}" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
echo "[restore] restoring ${DUMP}"
pg_restore -d "${TARGET_DB}" --no-owner --no-privileges "${DUMP}"

echo "[restore] verifying row counts"
psql "${TARGET_DB}" -Atc "SELECT 'students: '   || count(*) FROM students;"
psql "${TARGET_DB}" -Atc "SELECT 'enrollments: '|| count(*) FROM enrollments;"
psql "${TARGET_DB}" -Atc "SELECT 'ledger: '     || count(*) FROM ledger_entries;"
psql "${TARGET_DB}" -Atc "SELECT 'audit: '      || count(*) FROM audit_log;"
echo "[restore] done"
