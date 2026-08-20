#!/usr/bin/env bash
# SMS database backup (design §13 / spec §37).
#
#   ops/backup.sh [--dir /path/to/backups] [--s3 s3://bucket/prefix]
#
# Produces a custom-format pg_dump (parallel-restorable, schema+data) plus a
# SHA-256 manifest, then applies retention: 14 dailies / 8 weeklies / 12 monthlies.
# Off-site: pass --s3 (uses aws CLI or rclone if present) — never rely on the
# local copy alone (spec §37).
set -euo pipefail

BACKUP_DIR="/var/backups/sms"
S3_TARGET=""
DB_URL="${DATABASE_URL:?set DATABASE_URL, e.g. postgresql://sms_app:***@localhost:5432/sms}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dir) BACKUP_DIR="$2"; shift 2 ;;
    --s3)  S3_TARGET="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
DAY="$(date -u +%Y%m%d)"
mkdir -p "${BACKUP_DIR}/daily" "${BACKUP_DIR}/weekly" "${BACKUP_DIR}/monthly"

OUT="${BACKUP_DIR}/daily/sms-${STAMP}.dump"
echo "[backup] dumping to ${OUT}"
pg_dump -Fc -d "${DB_URL}" -f "${OUT}"
sha256sum "${OUT}" > "${OUT}.sha256"

# weekly/monthly copies
DOW="$(date -u +%u)"   # 1 = Monday
if [[ "${DOW}" == "1" ]]; then
  cp "${OUT}" "${OUT}.sha256" "${BACKUP_DIR}/weekly/"
fi
if [[ "${DAY}" == "01" ]]; then
  cp "${OUT}" "${OUT}.sha256" "${BACKUP_DIR}/monthly/"
fi

# off-site copy (strongly recommended)
if [[ -n "${S3_TARGET}" ]]; then
  if command -v aws >/dev/null 2>&1; then
    aws s3 cp "${OUT}" "${S3_TARGET}/daily/"
    aws s3 cp "${OUT}.sha256" "${S3_TARGET}/daily/"
  elif command -v rclone >/dev/null 2>&1; then
    rclone copy "${OUT}" "${S3_TARGET}/daily/"
    rclone copy "${OUT}.sha256" "${S3_TARGET}/daily/"
  else
    echo "[backup] WARNING: --s3 given but neither aws nor rclone found" >&2
  fi
fi

# retention: 14 daily / 8 weekly / 12 monthly
prune() {
  local dir="$1" keep="$2"
  ls -1t "${dir}"/sms-*.dump 2>/dev/null | tail -n +"$((keep + 1))" | while read -r f; do
    rm -f "$f" "${f}.sha256"
    echo "[backup] pruned ${f}"
  done
}
prune "${BACKUP_DIR}/daily" 14
prune "${BACKUP_DIR}/weekly" 8
prune "${BACKUP_DIR}/monthly" 12

echo "[backup] done: ${OUT}"
