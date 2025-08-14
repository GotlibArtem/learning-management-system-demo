import csv
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandParser

from users.services import UserImporter, UserImporterException


class Command(BaseCommand):
    help = "Import users from file"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--data", type=str)
        parser.add_argument("--skip-existent", type=bool, default=True)

    def handle(self, *args: Any, **options: Any) -> str | None:
        with Path(options["data"]).open() as data:
            reader = csv.DictReader(data, delimiter=";")
            for row in reader:
                try:
                    UserImporter(data=row, skip_if_user_exists=options["skip_existent"])()
                except UserImporterException as e:
                    self.stderr.write(self.style.ERROR(f"Can't import user: {row}, {e}"))
