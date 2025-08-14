from dataclasses import dataclass
from datetime import date, datetime

import sentry_sdk
from django.db.transaction import atomic
from django.utils import timezone

from app.services import BaseService
from product_access.models import ProductAccess
from products.models import Product
from users.models import User


class AccessProviderWarning(Exception):
    """Use to send warnings to sentry"""


@dataclass
class ProductAccessProvider(BaseService):
    product: Product
    user: User
    start_date: date
    end_date: date | None
    order_id: str
    access_granted_time: datetime

    @atomic
    def act(self) -> ProductAccess:
        try:
            access = ProductAccess.objects.select_for_update().get(order_id=self.order_id)
            self.fill_in_empty_access(access)
            self.update_existent_access(access)
        except ProductAccess.DoesNotExist:
            access = ProductAccess.objects.create(**self.update_kwargs)

        from product_access.services import UserProductAccessCacheInvalidator

        UserProductAccessCacheInvalidator(user=self.user)()

        return access

    @property
    def update_kwargs(self) -> dict:
        return {
            "order_id": self.order_id,
            "product": self.product,
            "user": self.user,
            "start_date": timezone.make_aware(datetime.combine(self.start_date, datetime.min.time()), timezone.get_default_timezone()),
            "end_date": timezone.make_aware(datetime.combine(self.end_date, datetime.max.time()), timezone.get_default_timezone()) if self.end_date else None,
            "granted_at": self.access_granted_time,
            "revoked_at": None,
        }

    def update_existent_access(self, access: ProductAccess) -> None:
        if self.should_be_updated(access):
            access.update_from_kwargs(**self.update_kwargs)
            access.save()
        else:
            sentry_sdk.capture_message(
                f"Event for order {self.order_id} is out of turn ({self.access_granted_time.isoformat()})",
            )

    def should_be_updated(self, access: ProductAccess) -> bool:
        is_current_granted_time_in_past = access.granted_at is None or access.granted_at < self.access_granted_time
        is_current_revoked_time_in_past = access.revoked_at is None or access.revoked_at < self.access_granted_time
        return is_current_granted_time_in_past and is_current_revoked_time_in_past

    def fill_in_empty_access(self, access: ProductAccess) -> None:
        # The following case is possible:
        # 1. lms shop sends event for granting access,
        # 2. after that it sends event for revoking access,
        # 3. but LMS receives those events in the reversed order.
        # In this case lms shouldn't grant access to user. The only way it's can be guaranted
        # is creating empty access on getting revoke event. And after that filling it with data
        # while processing event of access granting.
        if access.user is None and access.product is None:
            access.user = self.update_kwargs["user"]
            access.product = self.update_kwargs["product"]
            access.start_date = self.update_kwargs["start_date"]
            access.end_date = self.update_kwargs["end_date"]
            access.granted_at = self.access_granted_time
            access.save()
