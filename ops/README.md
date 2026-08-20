# ops/ — operational scripts

| Script | Purpose |
|---|---|
| `backup.sh` | `pg_dump -Fc` + SHA-256 manifest, daily/weekly/monthly retention, optional S3 off-site |
| `restore.sh` | Restore a backup dump into a target DB (checksum-verified, guarded) |
| `dr-drill.sh` | Quarterly DR drill: restore latest backup into scratch DB + integrity checks |

Full procedures: [../docs/runbooks/deployment.md](../docs/runbooks/deployment.md)

All scripts require `DATABASE_URL` (and `--s3`/`--target-db`/`SCRATCH_DB` as
relevant). Backups are only as good as your last tested restore — run the drill.
