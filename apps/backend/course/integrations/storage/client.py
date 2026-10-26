"""Private object storage. Never expose service credentials to the browser."""

import os
import boto3
from botocore.config import Config
from django.conf import settings


def client(category, public=False):
    prefix = "S3_" + category.upper()
    return boto3.client(
        "s3",
        endpoint_url=settings.S3_PUBLIC_ENDPOINT_URL
        if public
        else settings.S3_ENDPOINT_URL,
        region_name=settings.S3_REGION,
        aws_access_key_id=os.environ.get(
            prefix + "_ACCESS_KEY_ID", settings.S3_ACCESS_KEY_ID
        ),
        aws_secret_access_key=os.environ.get(
            prefix + "_SECRET_ACCESS_KEY", settings.S3_SECRET_ACCESS_KEY
        ),
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"},
            connect_timeout=5,
            read_timeout=60,
            retries={"max_attempts": 3, "mode": "standard"},
        ),
    )


def bucket(category):
    return settings.S3_BUCKETS[category]


def upload_url(asset):
    return client(asset.category, True).generate_presigned_url(
        "put_object",
        Params={
            "Bucket": bucket(asset.category),
            "Key": asset.staging_key,
            "ContentType": asset.content_type,
        },
        ExpiresIn=600,
    )


def download_url(asset, inline=False):
    from urllib.parse import quote

    return client(asset.category, True).generate_presigned_url(
        "get_object",
        Params={
            "Bucket": bucket(asset.category),
            "Key": asset.object_key,
            "ResponseContentType": asset.content_type,
            "ResponseContentDisposition": ("inline" if inline else "attachment")
            + "; filename*=UTF-8''"
            + quote(asset.name, safe=""),
        },
        ExpiresIn=300,
    )
