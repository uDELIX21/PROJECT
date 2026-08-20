# 13 · Backup/DR, Deployment & Observability

**Status:** Draft for approval · **Covers:** deliverable items 22–23 (+48 observability)

---

## 1. Backup & disaster recovery (REQ-BKP-01)

| Item | Design |
|---|---|
| Logical backup | `pg_dump -Fc` nightly (02:30 Africa/Accra) via cron container; compressed ~ estimated < 500 MB at 10× scale |
| Continuous protection | PostgreSQL WAL archiving to object storage (`pg_basebackup` + WAL-G) → point-in-time recovery (PITR) |
| File storage backup | object-store bucket versioning enabled; nightly manifest + integrity check |
| Retention | 14 dailies, 8 weeklies, 12 monthlies (configurable) |
| Off-site | backups encrypted (AES-256, keys held by school) and pushed to a **separate** S3-compatible bucket/account; restore keys stored offline with the school admin |
| Restore procedure | runbook in repo `docs/runbooks/restore.md`: provision → restore base backup → WAL replay to timestamp → verify row counts & hash-chain → switch DNS |
| Testing | **quarterly restore drill** scripted (`scripts/dr-drill.sh`) into a scratch cluster; results posted to admin health page (REQ-BKP-01 "periodic restoration testing") |
| Targets | RPO ≤ 5 min (WAL) / RTO ≤ 4 h single-VPS failure; documented in runbook |

---

## 2. Deployment architecture (single-VPS baseline, scale-ready)

```mermaid
flowchart TB
    subgraph Internet
        U[Users: phones & desktops]
        P[Payment/SMS providers]
    end
    subgraph VPS["Single VPS (4 vCPU / 8 GB recommended) — Docker Compose"]
        NG[nginx :443 TLS Let's Encrypt<br/>gzip/brotli, security headers]
        FE[Next.js standalone :3000]
        API[FastAPI uvicorn ×2 :8000]
        WKR[Worker: billing, reports,<br/>imports, SMS queue (arq)]
        PG[(PostgreSQL 16<br/>loopback bind)]
        RD[(Redis 7 loopback)]
        BK[Backup cron container]
    end
    S3[(Off-site S3-compatible<br/>backups + file storage)]
    U --> NG --> FE & API
    P --> API
    API --> PG & RD & S3
    WKR --> PG & RD & S3
    BK --> S3
```

- **Frontend** talks only to relative `/api/*` paths; nginx proxies to FastAPI (no CORS at all, preview-host friendly).
- **Stateless API** ⇒ horizontal scale path: add API/worker replicas behind a load balancer; Postgres → managed service with PITR when the school grows (REQ scale posture, spec §38).
- **Environments:** `dev` (docker compose, stub providers, ConsoleSMS), `staging` (prod-like + synthetic data), `prod`. Same images, env-only differences.
- **Migrations:** `alembic upgrade head` runs in the deploy pipeline before container switch; backups forced pre-migration.
- **Env documentation:** `.env.example` is the canonical list (DB URL, Redis URL, S3 endpoint/keys bucket name only, provider env-var names, session secret, CSRF secret, timezone, feature flags).

### Release process
Trunk-based on `arena/…` working branch → PR → CI (lint, type-check, tests, migration dry-run, frontend build + bundle budget) → staging auto-deploy → manual prod promotion with smoke checklist.

---

## 3. Observability (REQ-OBS-01)

| Pillar | Implementation |
|---|---|
| Structured logs | `structlog` JSON (request_id, user_id, duration); frontend: minimal error beacon | 
| Health checks | `/healthz` (process), `/healthz/ready` (DB SELECT 1, Redis PING, storage HEAD, provider configs present) — used by compose healthchecks & monitoring |
| Error monitoring | Sentry-compatible integration (self-hostable; optional) with PII scrubbing |
| Payment webhook monitor | unprocessed/invalid webhook counts (from `webhook_events`) + stale PENDING payments > 24 h → admin alerts panel |
| Sync monitor | `sync_mutations` REJECTED/CONFLICT rates per teacher/day → head dashboard "offline issues" widget |
| Queue monitor | worker queue depth + failed jobs (SMS retries, report batches) on admin status page |
| Admin status page | `/admin/system`: health matrix, backup last-success, audit hash-chain integrity, disk usage, queue stats — `VIEW_AUDIT`-level access |
| Uptime | external ping (cron-job style) against `/healthz` with SMS alert via the school's own provider once configured |

---

## 4. Operational runbooks (delivered in Phase 10)

`docs/runbooks/`: deployment, migration, restore, provider cutover (stub→live MoMo/SMS), term rollover checklist (close term → next year setup → billing run → promotion), import incident response, DR drill. Each includes the exact commands and rollback steps (REQ-ERR-01 spirit: operators get meaningful guidance too).
