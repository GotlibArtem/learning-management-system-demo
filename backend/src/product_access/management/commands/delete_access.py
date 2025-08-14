import csv
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandParser

from product_access.models import ProductAccess
from users.models import User


class Command(BaseCommand):
    help = "Delete product access based on user email and LMS ID from CSV file"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--data",
            type=str,
            help="Path to CSV file with useremail and lms_id columns",
            required=True,
        )
        parser.add_argument(
            "--output",
            type=str,
            help="Path to output file for logging missing entries",
            required=True,
        )

    def handle(self, *args: Any, **options: Any) -> None:
        missing_entries = []
        deleted_count = 0

        with Path(options["data"]).open() as data:
            reader = csv.DictReader(data, delimiter=",")

            for row in reader:
                user_email = row.get("useremail", "").strip()
                lms_id = row.get("lms_id", "").strip()

                if not user_email or not lms_id:
                    self.stderr.write(
                        self.style.ERROR(f"Invalid row format: {row}"),
                    )
                    continue

                try:
                    user = User.objects.get(username=user_email)
                    access = ProductAccess.objects.filter(
                        user=user,
                        product__id=lms_id,
                    )

                    if access.exists():
                        access.delete()
                        deleted_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Deleted access for user {user_email} and LMS ID {lms_id}",
                            ),
                        )
                    else:
                        missing_entries.append(
                            {
                                "useremail": user_email,
                                "lms_id": lms_id,
                                "reason": "Access not found",
                            },
                        )
                except User.DoesNotExist:
                    missing_entries.append(
                        {
                            "useremail": user_email,
                            "lms_id": lms_id,
                            "reason": "User not found",
                        },
                    )

        # Write missing entries to output file
        if missing_entries:
            with Path(options["output"]).open("w", newline="") as output_file:
                fieldnames = ["useremail", "lms_id", "reason"]
                writer = csv.DictWriter(output_file, fieldnames=fieldnames, delimiter=";")
                writer.writeheader()
                writer.writerows(missing_entries)

        self.stdout.write(
            self.style.SUCCESS(
                f"Deletion completed. Deleted {deleted_count} access records. Found {len(missing_entries)} missing entries.",
            ),
        )
