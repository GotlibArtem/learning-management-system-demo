import csv
from datetime import datetime
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandParser
from django.db import transaction

from users.models import User


class Command(BaseCommand):
    help = "Import user birthdays from CSV file"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--data", type=str, help="Path to CSV file with birthdays")
        parser.add_argument(
            "--output",
            type=str,
            help="Path to output CSV file for missed users",
            required=False,
        )

    def handle(self, *args: Any, **options: Any) -> str | None:
        missed_users = []
        with Path(options["data"]).open() as data:
            reader = csv.DictReader(data, delimiter=";")
            updated_count = 0
            skipped_count = 0

            for row in reader:
                with transaction.atomic():
                    email = row["Email"].strip()
                    birthday_str = row["Дата рождения"].strip()

                    try:
                        user = User.objects.get(username__iexact=email)
                        birthday = datetime.strptime(birthday_str, "%d.%m.%Y").date()  # noqa: DTZ007
                        user.birthdate = birthday
                        user.save(update_fields=["birthdate"])
                        updated_count += 1
                    except Exception:  # noqa: BLE001
                        self.stderr.write(
                            self.style.WARNING(f"User with email {email} not found"),
                        )
                        missed_users.append({"email": email, "reason": "user_not_found", **row})
                        skipped_count += 1

            if options.get("output") and missed_users:
                output_path = Path(options["output"])
                with output_path.open("w", newline="") as output_file:
                    if missed_users:
                        writer = csv.DictWriter(
                            output_file,
                            fieldnames=["email", "reason"] + list(missed_users[0].keys())[2:],
                            delimiter=";",
                        )
                        writer.writeheader()
                        writer.writerows(missed_users)
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Missed users written to {output_path}",
                            ),
                        )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully updated {updated_count} users' birthdays. Skipped {skipped_count} records.",
                ),
            )
