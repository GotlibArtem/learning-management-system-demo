from dataclasses import dataclass
from datetime import datetime

import sentry_sdk
from django.db.transaction import atomic
from django.utils import timezone

from app.exceptions import AppServiceException
from app.services import BaseService
from product_access.models import ProductAccess
from products.models import Product
from users.models import User


class TimedAccessProviderWarning(AppServiceException):
    """Use to send warnings to sentry"""


@dataclass
class TimedProductAccessProvider(BaseService):
    product: Product
    user: User
    start_at: datetime
    end_at: datetime | None
    order_id: str
    access_granted_time: datetime

    @atomic
    def act(self) -> ProductAccess:
        start_at = self._aware(self.start_at)
        end_at = self._aware(self.end_at) if self.end_at else None

        try:
            access = ProductAccess.objects.select_for_update().get(order_id=self.order_id)
            self.fill_in_empty_access(access, start_at, end_at)
            self.update_existent_access(access, start_at, end_at)
        except ProductAccess.DoesNotExist:
            access = ProductAccess.objects.create(
                order_id=self.order_id,
                product=self.product,
                user=self.user,
                start_date=start_at,
                end_date=end_at,
                granted_at=self.access_granted_time,
                revoked_at=None,
            )

        from product_access.services import UserProductAccessCacheInvalidator

        UserProductAccessCacheInvalidator(user=self.user)()

        return access

    def update_existent_access(self, access: ProductAccess, start_at: datetime, end_at: datetime | None) -> None:
        if self.should_be_updated(access):
            access.product = self.product
            access.user = self.user
            access.start_date = start_at
            access.end_date = end_at
            access.granted_at = self.access_granted_time
            access.revoked_at = None
            access.save()
        else:
            sentry_sdk.capture_message(
                f"Promo event for order {self.order_id} is out of turn ({self.access_granted_time.isoformat()})",
            )

    def should_be_updated(self, access: ProductAccess) -> bool:
        is_current_granted_time_in_past = access.granted_at is None or access.granted_at < self.access_granted_time
        is_current_revoked_time_in_past = access.revoked_at is None or access.revoked_at < self.access_granted_time
        return is_current_granted_time_in_past and is_current_revoked_time_in_past

    def fill_in_empty_access(self, access: ProductAccess, start_at: datetime, end_at: datetime | None) -> None:
        if access.user is None and access.product is None:
            access.user = self.user
            access.product = self.product
            access.start_date = start_at
            access.end_date = end_at
            access.granted_at = self.access_granted_time
            access.save()

    @staticmethod
    def _aware(dt: datetime) -> datetime:
        return dt if timezone.is_aware(dt) else timezone.make_aware(dt, timezone.get_default_timezone())
