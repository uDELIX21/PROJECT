#!/usr/bin/env bash
# SQLite restore — dev/CI equivalent of restore.sh. Verifies the SHA-256
# manifest, then copies the backup over the target DB and runs integrity +
# row-count checks. Guarded (needs --yes).
#
#   ops/restore_sqlite.sh <backup-file> [--db path/to/target.db] [--yes]
set -euo pipefail

BACKUP="${1:?usage: ops/restore_sqlite.sh <backup-file> [--db target.db] [--yes]}"
DB_PATH="backend/dev.db"
CONFIRMED=0

shift
while [[ $# -gt 0 ]]; do
  case "$1" in
    --db)  DB_PATH="$2"; shift 2 ;;
    --yes) CONFIRMED=1; shift ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

[[ -f "${BACKUP}" ]] || { echo "backup not found: ${BACKUP}" >&2; exit 1; }

if [[ -f "${BACKUP}.sha256" ]]; then
  ( cd "$(dirname "${BACKUP}")" && sha256sum -c "$(basename "${BACKUP}").sha256" )
else
  echo "[restore] WARNING: no checksum manifest; skipping verification" >&2
fi

if [[ "${CONFIRMED}" != "1" ]]; then
  echo "About to OVERWRITE ${DB_PATH} with ${BACKUP}"
  read -r -p "Type RESTORE to continue: " ans
  [[ "${ans}" == "RESTORE" ]] || { echo "aborted"; exit 1; }
fi

mkdir -p "$(dirname "${DB_PATH}")"
# IMPORTANT: stop the application server before restoring. Any WAL/SHM left by
# a running process is replayed over the restored file and can undo the restore.
if [[ -f "${DB_PATH}-wal" || -f "${DB_PATH}-shm" ]]; then
  echo "[restore] removing stale WAL/SHM (server must be stopped)"
  rm -f "${DB_PATH}-wal" "${DB_PATH}-shm"
fi
cp "${BACKUP}" "${DB_PATH}"

echo "[restore] verifying integrity + row counts"
python3 - "$DB_PATH" <<'PY'
import sqlite3, sys
c = sqlite3.connect(sys.argv[1])
ic = c.execute("PRAGMA integrity_check;").fetchone()[0]
print("integrity:", ic)
for label, table in [("students","students"), ("enrollments","enrollments"),
                     ("ledger","ledger_entries"), ("audit","audit_log")]:
    try:
        n = c.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
        print(f"{label}: {n}")
    except sqlite3.Error as e:
        print(f"{label}: ERROR {e}")
c.close()
PY
echo "[restore] done"
