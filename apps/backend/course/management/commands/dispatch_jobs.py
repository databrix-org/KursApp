from datetime import timedelta
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils import timezone
from course.models import Job
from course.tasks import run_job


class Command(BaseCommand):
    help = "Redispatch persisted pending, retryable failed, or stale worker jobs."

    def add_arguments(self, p):
        p.add_argument("--job-id")
        p.add_argument("--retry-exhausted", action="store_true")

    def handle(self, *args, **options):
        if options["retry_exhausted"]:
            if not options["job_id"]:
                raise CommandError("Select one reviewed job with --job-id")
            Job.objects.filter(pk=options["job_id"], status="failed").update(attempts=0)

        q = Q(status__in=["pending", "failed"]) | Q(
            status="running", updated_at__lt=timezone.now() - timedelta(minutes=10)
        )
        jobs = Job.objects.filter(q, attempts__lt=5)
        if options["job_id"]:
            jobs = jobs.filter(pk=options["job_id"])
        ids = list(jobs.values_list("pk", flat=True))
        for pk in ids:
            run_job.delay(str(pk))
        self.stdout.write(f"Dispatched {len(ids)} persisted jobs")
