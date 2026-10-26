#!/usr/bin/env python3
"""Run via uv with backend dependencies. Uses only an explicitly supplied isolated test bucket."""

import argparse, hashlib, os, sys, uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "apps/backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()
from course.integrations.storage.client import client
from botocore.exceptions import ClientError
from urllib.request import Request, urlopen
from urllib.error import HTTPError

p = argparse.ArgumentParser()
p.add_argument("--bucket", required=True)
p.add_argument("--category", default="notebooks")
p.add_argument("--confirm-isolated-test-bucket", action="store_true")
o = p.parse_args()
if not o.confirm_isolated_test_bucket:
    p.error("Explicit isolated test bucket confirmation required")
s3 = client(o.category)
public = client(o.category, True)
key = "acceptance/" + str(uuid.uuid4()) + "/probe.bin"
data = b"databrix-storage-acceptance-0123456789"
url = public.generate_presigned_url(
    "put_object",
    Params={"Bucket": o.bucket, "Key": key, "ContentType": "application/octet-stream"},
    ExpiresIn=60,
)
with urlopen(
    Request(
        url,
        data=data,
        method="PUT",
        headers={"Content-Type": "application/octet-stream"},
    )
) as r:
    assert r.status in (200, 204)
get = public.generate_presigned_url(
    "get_object", Params={"Bucket": o.bucket, "Key": key}, ExpiresIn=60
)
with urlopen(Request(get, headers={"Range": "bytes=0-7"})) as r:
    assert r.status == 206 and r.read() == data[:8]
try:
    s3.put_object(Bucket=o.bucket, Key=key, Body=b"overwrite", IfNoneMatch="*")
except ClientError as e:
    assert e.response["Error"]["Code"] in ("412", "PreconditionFailed")
else:
    raise AssertionError("Endpoint allowed a conditional overwrite")
body = s3.get_object(Bucket=o.bucket, Key=key)["Body"]
assert hashlib.sha256(body.read()).digest() == hashlib.sha256(data).digest()
body.close()
assert s3.get_bucket_versioning(Bucket=o.bucket).get("Status") == "Enabled", (
    "Enable versioning and test provider recovery"
)
versions = s3.list_object_versions(Bucket=o.bucket, Prefix=key).get("Versions", [])
assert versions
restored = s3.get_object(Bucket=o.bucket, Key=key, VersionId=versions[0]["VersionId"])[
    "Body"
]
assert restored.read() == data
restored.close()
# Anonymous object access must fail even when its key is known.
try:
    urlopen(Request(f"{public.meta.endpoint_url}/{o.bucket}/{key}"))
except HTTPError as e:
    assert e.code in (401, 403)
else:
    raise AssertionError("Object is publicly readable")
# Recover the original version after an isolated probe overwrite.
s3.put_object(Bucket=o.bucket, Key=key, Body=b"new-probe-version")
body = s3.get_object(Bucket=o.bucket, Key=key, VersionId=versions[0]["VersionId"])[
    "Body"
]
try:
    original = body.read()
finally:
    body.close()
assert original == data
s3.put_object(Bucket=o.bucket, Key=key, Body=original)
with urlopen(
    Request(
        get,
        method="OPTIONS",
        headers={
            "Origin": "http://127.0.0.1:8080",
            "Access-Control-Request-Method": "PUT",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )
) as r:
    assert r.headers.get("Access-Control-Allow-Origin") in (
        "http://127.0.0.1:8080",
        "*",
    )
print(
    "PASS: signed PUT/GET, byte ranges, conditional overwrite denial, private access, CORS, checksum, versioning and recovery"
)
print(
    "Probe retained in isolated test bucket. Review production retention and credential policies separately."
)
