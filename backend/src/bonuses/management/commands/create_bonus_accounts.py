from django.core.management.base import BaseCommand

from bonuses.models import BonusAccount
from users.models import User


BATCH_SIZE = 1000


class Command(BaseCommand):
    help = "Create bonus accounts for all existing users who don't have one."

    def handle(self, *args, **options):
        users_without_accounts = User.objects.filter(bonus_account__isnull=True)

        if not users_without_accounts.exists():
            self.stdout.write(self.style.SUCCESS("All users already have bonus accounts."))
            return

        total = users_without_accounts.count()
        self.stdout.write(self.style.WARNING(f"Creating bonus accounts for {total} users..."))

        bonus_accounts = []

        for user in users_without_accounts.iterator():
            bonus_accounts.append(BonusAccount(user=user))

            if len(bonus_accounts) >= BATCH_SIZE:
                BonusAccount.objects.bulk_create(bonus_accounts, batch_size=BATCH_SIZE)
                bonus_accounts.clear()

        if bonus_accounts:
            BonusAccount.objects.bulk_create(bonus_accounts, batch_size=BATCH_SIZE)

        self.stdout.write(self.style.SUCCESS(f"Successfully created {total} bonus accounts."))
