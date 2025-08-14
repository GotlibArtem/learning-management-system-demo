from dataclasses import dataclass

from django.conf import settings
from django.core.cache import cache

from app.services import BaseService
from product_access.models import ProductAccess
from users.models import User


@dataclass
class UserSubscriptionChecker(BaseService):
    """
    Check if user has active subscription
    """

    user: User

    def act(self) -> bool:
        if settings.CACHE_ENABLED:
            return cache.get_or_set(  # type: ignore[return-value]
                f"user_subscription_checker_{self.user.id}",
                self.check_user_subscription,
                timeout=settings.CACHE_DURATION_SECONDS,
            )

        return self.check_user_subscription()

    def check_user_subscription(self) -> bool:
        return ProductAccess.objects.active_for_user(self.user).filter(product__product_type="subscription").exists()
