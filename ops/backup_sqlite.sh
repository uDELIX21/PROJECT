#!/usr/bin/env bash
# SQLite backup — dev/CI equivalent of backup.sh (which targets PostgreSQL in
# production). Uses Python's sqlite3 online backup API (safe against concurrent
# writes) plus a SHA-256 manifest and daily/weekly/monthly retention.
#
#   ops/backup_sqlite.sh [--db path/to/dev.db] [--dir /path/to/backups]
set -euo pipefail

DB_PATH="backend/dev.db"
BACKUP_DIR="backups"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --db)  DB_PATH="$2"; shift 2 ;;
    --dir) BACKUP_DIR="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

[[ -f "${DB_PATH}" ]] || { echo "db not found: ${DB_PATH}" >&2; exit 1; }

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
DAY="$(date -u +%Y%m%d)"
mkdir -p "${BACKUP_DIR}/daily" "${BACKUP_DIR}/weekly" "${BACKUP_DIR}/monthly"

OUT="${BACKUP_DIR}/daily/sms-${STAMP}.sqlite3"
echo "[backup] online backup of ${DB_PATH} → ${OUT}"
python3 - "$DB_PATH" "$OUT" <<'PY'
import sqlite3, sys
src, dst = sys.argv[1], sys.argv[2]
s = sqlite3.connect(src)
d = sqlite3.connect(dst)
with d:
    s.backup(d)
d.close(); s.close()
PY
sha256sum "${OUT}" > "${OUT}.sha256"

DOW="$(date -u +%u)"
if [[ "${DOW}" == "1" ]]; then cp "${OUT}" "${OUT}.sha256" "${BACKUP_DIR}/weekly/"; fi
if [[ "${DAY}" == "01" ]]; then cp "${OUT}" "${OUT}.sha256" "${BACKUP_DIR}/monthly/"; fi

prune() {
  local dir="$1" keep="$2"
  ls -1t "${dir}"/sms-*.sqlite3 2>/dev/null | tail -n +"$((keep + 1))" | while read -r f; do
    rm -f "$f" "${f}.sha256"; echo "[backup] pruned ${f}"
  done
}
prune "${BACKUP_DIR}/daily" 14
prune "${BACKUP_DIR}/weekly" 8
prune "${BACKUP_DIR}/monthly" 12

echo "[backup] done: ${OUT}"
