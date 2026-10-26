#!/usr/bin/env python3
"""Local-only app recreation and fresh PostgreSQL restore; never removes durable volumes."""

import argparse, subprocess, time, urllib.request

p = argparse.ArgumentParser()
p.add_argument("--confirm-local-demo", action="store_true")
o = p.parse_args()
if not o.confirm_local_demo:
    p.error("Explicit local demo confirmation required")


def run(args, **kw):
    return subprocess.run(["docker", "compose", *args], check=True, **kw)


probe = "from django.apps import apps; from django.core import serializers; from course.models import Job; import hashlib,json; models=[m for m in apps.get_app_config('course').get_models() if m is not Job]; data={m._meta.label:serializers.serialize('json',m.objects.order_by('pk')) for m in models}; data['durable_jobs']=json.dumps(list(Job.objects.order_by('pk').values('id','kind','payload')),default=str,sort_keys=True); print(json.dumps({'rows':{m._meta.label:m.objects.count() for m in models},'fingerprint':hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()},sort_keys=True))"


def snapshot():
    return run(
        ["exec", "-T", "backend", "python", "manage.py", "shell", "-c", probe],
        capture_output=True,
        text=True,
    ).stdout.splitlines()[-1]


guard = run(
    [
        "exec",
        "-T",
        "backend",
        "python",
        "manage.py",
        "shell",
        "-c",
        "from django.conf import settings; assert settings.DEBUG and settings.DATABASES['default']['HOST']=='postgres' and settings.DATABASES['default']['NAME']=='databrix', 'Local demo database required'",
    ],
    capture_output=True,
    text=True,
)
before = snapshot()
run(
    [
        "--profile",
        "local",
        "up",
        "-d",
        "--force-recreate",
        "postgres",
        "redis",
        "storage",
        "backend",
        "worker",
        "dispatcher",
        "web",
        "proxy",
    ]
)
for _ in range(60):
    try:
        if (
            urllib.request.urlopen("http://127.0.0.1:8080/readyz/", timeout=2).status
            == 200
        ):
            break
    except Exception:
        time.sleep(1)
else:
    raise RuntimeError("Recreated stack did not become ready")
assert snapshot() == before, "Container recreation changed academic state"
run(
    [
        "exec",
        "-T",
        "backend",
        "python",
        "manage.py",
        "reconcile_artifacts",
        "--output",
        "/tmp/recreate-" + str(int(time.time())) + ".json",
    ]
)
# Restore into a new database, retaining both source and restore databases for review.
name = "rehearsal_" + str(int(time.time()))
dump = run(
    ["exec", "-T", "postgres", "pg_dump", "-U", "databrix", "-d", "databrix", "-Fc"],
    capture_output=True,
).stdout
run(["exec", "-T", "postgres", "createdb", "-U", "databrix", name])
run(
    [
        "exec",
        "-T",
        "postgres",
        "pg_restore",
        "-U",
        "databrix",
        "-d",
        name,
        "--no-owner",
    ],
    input=dump,
)
restored = run(
    [
        "run",
        "--rm",
        "-T",
        "-e",
        "DATABASE_URL=postgres://databrix:local-database-password@postgres:5432/"
        + name,
        "backend",
        "python",
        "manage.py",
        "shell",
        "-c",
        probe,
    ],
    capture_output=True,
    text=True,
).stdout.splitlines()[-1]
assert restored == before, "Restored database metadata differs"
run(
    [
        "run",
        "--rm",
        "-T",
        "-e",
        "DATABASE_URL=postgres://databrix:local-database-password@postgres:5432/"
        + name,
        "backend",
        "python",
        "manage.py",
        "reconcile_artifacts",
        "--output",
        "/tmp/restored.json",
    ]
)
print(
    "PASS: app recreation, preserved academic records/artifact hashes, fresh PostgreSQL restore, full artifact reconciliation"
)
print("Restored isolated database retained:", name)
