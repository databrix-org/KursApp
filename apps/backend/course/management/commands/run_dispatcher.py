import time
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Redispatch durable pending/failed jobs and recover expired worker leases"

    def handle(self, *args, **options):
        while True:
            try:
                call_command("dispatch_jobs")
            except Exception:
                self.stderr.write("Broker unavailable; retrying durable jobs")
            time.sleep(30)
