from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from botocore.exceptions import ClientError
from course.integrations.storage.client import client


class Command(BaseCommand):
    help = "Initialize DEVELOPMENT buckets and browser CORS; never changes production bucket policies."

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError(
                "Configure production buckets through your storage operator"
            )
        for category, bucket in settings.S3_BUCKETS.items():
            s3 = client(category)
            try:
                s3.head_bucket(Bucket=bucket)
            except ClientError:
                args = {"Bucket": bucket}
                if settings.S3_REGION != "us-east-1":
                    args["CreateBucketConfiguration"] = {
                        "LocationConstraint": settings.S3_REGION
                    }
                s3.create_bucket(**args)
            s3.put_bucket_versioning(
                Bucket=bucket, VersioningConfiguration={"Status": "Enabled"}
            )
            try:
                s3.put_bucket_cors(
                    Bucket=bucket,
                    CORSConfiguration={
                        "CORSRules": [
                            {
                                "AllowedOrigins": settings.CSRF_TRUSTED_ORIGINS,
                                "AllowedMethods": ["GET", "PUT", "HEAD"],
                                "AllowedHeaders": ["Content-Type", "Range"],
                                "ExposeHeaders": [
                                    "ETag",
                                    "Content-Length",
                                    "Content-Range",
                                ],
                                "MaxAgeSeconds": 600,
                            }
                        ]
                    },
                )
            except ClientError as exc:
                if exc.response["Error"]["Code"] != "NotImplemented":
                    raise
                self.stdout.write(
                    "Endpoint uses service-level CORS; local MinIO config supplies the platform origins"
                )
            self.stdout.write(f"{category}: initialized")
