# Deployment & Operations Runbook (Phase 10)

Production deployment, migration, seed, backup/restore, and troubleshooting for
the SMS. Target: single VPS behind nginx, Docker Compose (design §13).

```
Internet ──► nginx :443 (TLS) ──► Next.js :3000 (UI)
                              └──► FastAPI :8000 (API, proxied at /api)
                                       ├── PostgreSQL 16 (loopback only)
                                       ├── Redis 7 (loopback only)
                                       └── S3-compatible storage (files/backups)
```

## 1. Prerequisites

- VPS: 4 vCPU / 8 GB RAM / 40 GB disk (10× headroom over the 700-student target)
- Docker + Docker Compose v2
- A DNS name (e.g. `sms.school.edu.gh`) pointed at the server
- TLS via Let's Encrypt (certbot) or your CA
- Off-site object storage (any S3-compatible) for backups + file store

## 2. Environment variables (spec: env-var documentation)

Copy `backend/.env.example` to `backend/.env` and set for production. The
critical production values:

| Variable | Production value | Notes |
|---|---|---|
| `ENVIRONMENT` | `prod` | disables dev conveniences |
| `DEV_MODE` | `false` | hides API docs + dev reset tokens |
| `DATABASE_URL` | `postgresql+psycopg://sms_app:…@db:5432/sms` | inside Compose network |
| `SESSION_COOKIE_SECURE` | `true` | HTTPS only |
| `SESSION_COOKIE_DOMAIN` | your domain | |
| `ARGON_TIME_COST` / `ARGON_MEMORY_COST_KIB` | `3` / `65536` | OWASP-recommended |
| `RATELIMIT_ENABLED` | `true` | |
| `SMS_WEBHOOK_SECRET` | strong random | payment webhook HMAC |
| `SMS_STORAGE_DIR` / S3 vars | S3 bucket | file store |
| `comms.provider` (school setting) | `ARKesel`/`HUBTEL` | live SMS (env creds) |

Secrets live **only** in env / secret manager — never in the DB or frontend
(REQ-SEC-02, Agent Rule 11).

## 3. First deploy

```bash
git clone <repo> && cd PROJECT
cp backend/.env.example backend/.env   # edit for production

# TLS (once): obtain certs into deploy/certs/{fullchain,privkey}.pem
sudo certbot certonly --standalone -d sms.school.edu.gh
# place/symlink into deploy/certs/

# set the Compose DB password
export POSTGRES_PASSWORD="$(openssl rand -base64 24)"

docker compose up -d --build
docker compose ps                       # all services healthy
curl -fsS http://localhost/healthz || true
curl -fsSk https://sms.school.edu.gh/healthz
```

## 4. Database migrations (Alembic)

Migrations are additive and run in the deploy pipeline **before** swapping the
app. The DB user for migrations needs DDL; the app runtime user should not.

```bash
# apply pending migrations (from backend/)
DATABASE_URL="postgresql+psycopg://sms_app:…@localhost:5432/sms" \
  alembic upgrade head

# check current revision
alembic current
# inspect a migration before applying
alembic show <revision>
```

Rules (design §04): additive changes preferred; destructive changes are
two-step (deprecate → drop); every migration ships a downgrade where feasible.
Always take a backup (§6) before running migrations in production.

## 5. Seeding

```bash
# Full realistic demo dataset (720 students, finance, reports) — FICTIONAL
DATABASE_URL=… alembic upgrade head
DATABASE_URL=… python scripts/seed.py --reset

# Smaller dev set
DATABASE_URL=… python scripts/seed.py --reset --fast
```

Seed data is **explicitly fictional** (REQ-SEED-02, Agent Rule 12). For a real
go-live you do **not** run the demo seed; instead bootstrap the catalog
(grades, roles, permissions, templates) and import the school's actual records
via the Imports module (Phase 8), starting with an opening-balance import.

## 6. Backups (spec §37)

Automated via cron; off-site via `--s3`.

```bash
# /etc/cron.d/sms-backup
15 2 * * *  root  /opt/sms/ops/backup.sh --s3 s3://school-sms-backups >> /var/log/sms-backup.log 2>&1
```

Retention is enforced by `ops/backup.sh`: **14 dailies / 8 weeklies / 12
monthlies**. Each dump gets a SHA-256 manifest for restore integrity.

## 7. Restore (disaster recovery)

```bash
# restore a specific dump into the target DB (destructive — prompts unless --yes)
DATABASE_URL="postgresql://sms_app:…@localhost:5432/sms" \
  ops/restore.sh /var/backups/sms/daily/sms-20260820T021500Z.dump

# point-in-time (if WAL archiving is enabled) — recover to a timestamp
#   using your WAL archive tooling, then verify with the row-count checks.
```

> ⚠️ **Stop the application server before restoring.** A running process holds
> WAL/SHM state that is replayed over the restored file and can silently undo
> the restore. The SQLite helper removes stale WAL/SHM automatically; for
> PostgreSQL stop the app tier (or the postmaster) first.

### Dev/CI equivalent (SQLite)

```bash
ops/backup_sqlite.sh --db backend/dev.db --dir backups
ops/restore_sqlite.sh backups/daily/sms-…sqlite3 --db backend/dev.db --yes
```

## 8. Periodic restoration testing (spec §37)

Quarterly DR drill restores the latest backup into a **scratch** database and
verifies integrity without touching production:

```bash
SCRATCH_DB="postgresql://sms_app@localhost:5432/sms_drill" ops/dr-drill.sh
# → prints PASS/FAIL; wire into alerting
```

## 9. Health checks & monitoring (spec §48)

- `GET /healthz` — liveness
- `GET /healthz/ready` — DB connectivity (503 when down)
- Wire both into your uptime monitor (e.g. Uptime Kuma / external ping)
- Admin health view: `/settings` (school) + the comms SMS log surface provider
  failures; payment webhook failures appear as non-applied webhook events.

## 10. Troubleshooting (spec §47)

| Symptom | Likely cause | Action |
|---|---|---|
| `503 /healthz/ready` | DB unreachable | check `docker compose ps db`, disk space, `DATABASE_URL` |
| Login throttled | rate-limit/lockout | wait for lock window; admin can unlock via Users |
| Payment stuck `PENDING` | webhook not received/verified | check webhook log; verify `SMS_WEBHOOK_SECRET`; reconcile manually |
| Duplicate webhook warnings | provider retry | expected — idempotency dedupes; confirm single receipt |
| Report blocked | financial clearance | see clearance state; apply waiver/override (audited) if authorized |
| Import fails mid-commit | row error surfaced | job shows `ROLLED_BACK`; fix rows and re-upload (nothing saved) |
| Offline marks not syncing | network / auth expired | check SyncBadge; re-login; conflicts need manual resolution |
| SMS not sending | provider creds/quota | check comms provider + SMS log `FAILED` rows |

## 11. Rollback

```bash
# app rollback: redeploy previous image tag
docker compose up -d --build api web
# data rollback: restore last known-good backup (§7), then redeploy matching code
```

Keep code and schema in lockstep: never run new code against an old schema or
vice versa.
