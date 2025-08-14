import csv
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandParser

from product_access.services import DirectAccessImporter


class Command(BaseCommand):
    help = "Import direct access from file"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--data", type=str)

    def handle(self, *args: Any, **options: Any) -> str | None:
        with Path(options["data"]).open() as data:
            reader = csv.DictReader(data, delimiter=";")
            for row in reader:
                try:
                    DirectAccessImporter(data=row)()
                except Exception as e:  # noqa: BLE001
                    self.stderr.write(self.style.ERROR(f"Can't import product access: {row}, {e}"))
