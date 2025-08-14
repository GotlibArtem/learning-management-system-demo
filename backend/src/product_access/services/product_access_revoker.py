from dataclasses import dataclass
from datetime import datetime

import sentry_sdk
from django.db.transaction import atomic, on_commit
from django.utils import timezone

from app.services import BaseService
from product_access.models import ProductAccess


@dataclass
class ProductAccessRevoker(BaseService):
    order_id: str
    access_revoke_time: datetime

    @atomic
    def act(self) -> ProductAccess:
        try:
            access = ProductAccess.objects.select_for_update().get(order_id=self.order_id)
            if self.should_be_revoked(access):
                access.revoked_at = self.access_revoke_time
                access.save(update_fields=["revoked_at", "modified"])

                if access.user is not None:
                    from product_access.services import UserProductAccessCacheInvalidator

                    UserProductAccessCacheInvalidator(user=access.user)()

                return access
            sentry_sdk.capture_message(
                f"Event for order {self.order_id} is out of turn ({self.access_revoke_time.isoformat()})",
            )
        except ProductAccess.DoesNotExist:
            # The following case is possible:
            # 1. lms shop sends event for granting access,
            # 2. after that it sends event for revoking access,
            # 3. but LMS receives those events in the reversed order.
            # In this case lms shouldn't grant access to user. The only way it's can be guaranted
            # is creating empty access on getting revoke event. And after that filling it with data
            # while processing event of access granting.
            access = ProductAccess.objects.create(
                order_id=self.order_id,
                user=None,
                product=None,
                start_date=timezone.now().replace(hour=0, minute=0, second=0, microsecond=0),
                end_date=None,
                granted_at=None,
                revoked_at=self.access_revoke_time,
            )

        return access

    def should_be_revoked(self, access: ProductAccess) -> bool:
        is_current_granted_time_in_past = access.granted_at is None or access.granted_at < self.access_revoke_time
        is_current_revoked_time_in_past = access.revoked_at is None or access.revoked_at < self.access_revoke_time
        return is_current_granted_time_in_past and is_current_revoked_time_in_past
