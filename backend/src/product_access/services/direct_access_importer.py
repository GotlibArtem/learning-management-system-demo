import uuid
import zoneinfo
from dataclasses import dataclass
from datetime import date, datetime

from django.db.transaction import atomic
from django.utils import timezone
from django.utils.functional import cached_property

from app.services import BaseService
from product_access.models import ProductAccess
from product_access.services.product_checkout_processor import ProductCheckoutProcessor


@dataclass
class DirectAccessImporter(BaseService):
    data: dict

    @atomic
    def act(self) -> None:
        if self.data["name"].lower().startswith("подписка"):
            return None

        ProductCheckoutProcessor(checkout_event=self.checkout_event)()

        # update creation time so that access granted during import can be removed based on this value
        self.created_access.created = datetime(2024, 1, 1, tzinfo=zoneinfo.ZoneInfo("UTC"))
        self.created_access.save(update_fields=["created", "modified"])

    @property
    def checkout_event(self) -> dict:
        return {
            "event_id": str(uuid.uuid4()),
            "event_type": "order-checkedout",
            "event_time": timezone.now(),
            "data": {
                "order_id": self.data["orderId"],
                "user": {
                    "username": self.data["username"].strip().lower(),
                    "first_name": self.data["firstName"].strip(),
                    "last_name": self.data["lastName"].strip(),
                },
                "start_date": self.start_date,
                "end_date": None,
                "product": {
                    "shop_id": self.data["shopId"],
                    "lms_id": self.data["lmsId"],
                    "name": self.data["name"].strip(),
                },
            },
        }

    @property
    def start_date(self) -> date:
        return date.fromisoformat(self.data["startDate"])

    @cached_property
    def created_access(self) -> ProductAccess:
        return ProductAccess.objects.get(order_id=self.data["orderId"])
