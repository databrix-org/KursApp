# Backup, restore, and durable artifacts

Back up PostgreSQL and its referenced object set as a coordinated recovery point.
Retain database encryption keys/configuration separately from images and source control.
Use provider-native versioning/replication or an independently protected object backup.
The application never automatically expires accepted artifacts while grades reference them.

## Database backup

For the local Compose database:

```bash
umask 077
mkdir -p backups
docker compose exec -T postgres pg_dump -U databrix -d databrix -Fc > backups/databrix.dump
```

Use restrictive directory/file permissions and encrypted off-host copies for real student data.
For managed PostgreSQL, follow the provider's snapshot/PITR mechanism and verify a fresh restore.
Store the image digests, schema migration list, configuration version, asset reconciliation report,
and database backup identifier in the release's recovery manifest.
Never put secrets or signed URLs in that manifest.

## Restore rehearsal

1. Pause mutations and workers/dispatcher; record the last accepted submission and grade revision IDs.
2. Restore the database into a new isolated PostgreSQL database, using a different URL from production.
3. Restore/protect the object versions referenced at that database recovery point.
4. Run migrations only for the selected application version.
5. Run `python manage.py reconcile_artifacts --output /tmp/restore-reconciliation.json`.
6. Compare records, scores, feedback, roster/material manifests, and accepted-file SHA-256 values.
7. Verify unauthorized reads remain denied, MP4 range requests work, and students can read their receipts.
8. Recreate application containers and repeat reconciliation before allowing new submissions.
9. Record measured recovery time and any missing objects; do not silently clear broken references or grades.

`reconcile_artifacts` is read-only and returns failure for a missing or changed object.
A lost file requires object recovery; deleting its database row is not recovery.
Retain originals/migration reports until the restored object set and academic records reconcile.

## Broker or worker failure

Job rows persist in PostgreSQL. Redis AOF improves broker durability but is not the only source of job state.
The dispatcher retries pending/failed work and recovers leases older than ten minutes.
A storage outage leaves a submission validating; it does not erase grades or accept incomplete artifacts.
Inspect Job errors and provider health, then use `dispatch_jobs` after resolving the outage.
Repeated permanent failures require operator review; never change status to accepted without verification.

## DHBW recovery is independent

Databrix recovery restores course metadata and accepted snapshots only.
Provider-managed Hub state and editable workspace folders require DHBW's own backup/restore process.
Restoring one environment does not restore or rewrite the other.

For an exhausted, individually reviewed failed job, use
`python manage.py dispatch_jobs --job-id JOB_UUID --retry-exhausted` after resolving the provider failure.
