from dataclasses import dataclass

from django.conf import settings
from django.core.cache import cache

from app.services import BaseService
from payments.models import Recurrent, RecurrentStatus
from product_access.models import ProductAccess
from users.models import User


@dataclass
class UserRecurringSubscriptionChecker(BaseService):
    """
    Check if user has:
    - any active subscription to specific product,
    - an active Recurrent tied to a subscription product.
    """

    user: User

    def act(self) -> bool:
        if settings.CACHE_ENABLED:
            return cache.get_or_set(  # type: ignore[return-value]
                f"user_recurring_subscription_checker_{self.user.id}",
                self.check_recurring_subscription,
                timeout=settings.CACHE_DURATION_SECONDS,
            )

        return self.check_recurring_subscription()

    def check_recurring_subscription(self) -> bool:
        return self._has_active_subscription_access() and self._has_active_recurrent_subscription()

    def _has_active_subscription_access(self) -> bool:
        return ProductAccess.objects.active_for_user(self.user).filter(product__product_type="subscription").exists()

    def _has_active_recurrent_subscription(self) -> bool:
        return Recurrent.objects.filter(
            user=self.user,
            status=RecurrentStatus.ACTIVE,
            product__product_type="subscription",
        ).exists()
