from django.core.management.base import BaseCommand, CommandError
from course.models import Identity, CustomUserModel


class Command(BaseCommand):
    help = "Operator-reviewed binding of verified institution subject to an existing user ID"

    def add_arguments(self, p):
        p.add_argument("--user-id", type=int, required=True)
        p.add_argument("--issuer", required=True)
        p.add_argument("--subject", required=True)

    def handle(self, *args, **o):
        user = CustomUserModel.objects.get(pk=o["user_id"])
        identity, created = Identity.objects.get_or_create(
            issuer=o["issuer"], subject=o["subject"], defaults={"user": user}
        )
        if identity.user_id != user.pk:
            raise CommandError("Identity already belongs to another user")
        self.stdout.write(
            "Identity linked; existing account and academic history retained"
        )
