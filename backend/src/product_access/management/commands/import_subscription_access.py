import csv
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandParser

from product_access.services import SubscriptionAccessImporter
from products.models import Product


class Command(BaseCommand):
    help = "Import subscription access from file"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--data", type=str)
        parser.add_argument("--product_id", type=str)

    def handle(self, *args: Any, **options: Any) -> str | None:
        product = Product.objects.get(id=options["product_id"])
        with Path(options["data"]).open() as data:
            reader = csv.DictReader(data, delimiter=";")
            for row in reader:
                try:
                    SubscriptionAccessImporter(data=row, product=product)()
                except Exception as e:  # noqa: BLE001
                    self.stderr.write(self.style.ERROR(f"Can't import subscription access: {row}, {e}"))
