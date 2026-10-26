from datetime import timedelta
from celery import shared_task
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from course.models import Job, Submission, Asset
from course.services.submissions import validate_asset, check_deadline_date


@shared_task(bind=True, max_retries=3, acks_late=True)
def run_job(self, job_id):
    with transaction.atomic():
        job = Job.objects.select_for_update().get(pk=job_id)
        if job.status == "completed":
            return
        if job.status == "running" and job.updated_at > timezone.now() - timedelta(
            minutes=10
        ):
            return
        job.status = "running"
        job.attempts += 1
        job.save()
    try:
        if job.kind == "submission":
            sub = Submission.objects.select_related(
                "exercise__lesson__module__course"
            ).get(pk=job.payload["submission_id"])
            if sub.status != "accepted":
                check_deadline_date(sub.deadline_date, sub.finalized_at)
                if not sub.assets.exists():
                    raise ValidationError("No submission artifacts")
                for asset in sub.assets.all():
                    if asset.status != "accepted":
                        validate_asset(asset)
                with transaction.atomic():
                    sub = Submission.objects.select_for_update().get(pk=sub.pk)
                    sub.status = "accepted"
                    sub.accepted_at = timezone.now()
                    sub.rejection_reason = ""
                    sub.save()
        elif job.kind == "asset":
            validate_asset(Asset.objects.get(pk=job.payload["asset_id"]))
        elif job.kind == "email":
            from django.core.mail import send_mail
            from django.conf import settings

            send_mail(
                job.payload["subject"],
                job.payload["body"],
                settings.DEFAULT_FROM_EMAIL,
                job.payload["recipients"],
            )
        job.status = "completed"
        job.error = ""
        job.save()
    except ValidationError as exc:
        job.status = "rejected"
        job.error = "; ".join(exc.messages)[:255]
        job.save()
        if job.kind == "submission":
            Submission.objects.filter(pk=job.payload["submission_id"]).update(
                status="rejected", rejection_reason=job.error
            )
        elif job.kind == "asset":
            Asset.objects.filter(pk=job.payload["asset_id"]).update(status="rejected")
    except Exception as exc:
        job.status = "failed"
        job.error = "External operation failed; retry or inspect provider health"
        job.save()
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=10 * 2**self.request.retries)
        raise
