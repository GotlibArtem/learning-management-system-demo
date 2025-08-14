from dataclasses import dataclass
from datetime import datetime

from django.conf import settings
from django.core.cache import cache

from app.services import BaseService
from product_access.models import ProductAccess
from users.models import User


@dataclass
class SubscriptionBoundaries:
    start_date: datetime | None
    end_date: datetime | None


@dataclass
class SubscriptionBoundariesCalculator(BaseService):
    """
    Return end date of the last user subscription.
    """

    user: User

    def act(self) -> SubscriptionBoundaries | None:
        if settings.CACHE_ENABLED:
            boundaries_dict = cache.get_or_set(
                f"subscription_boundaries_{self.user.id}",
                self._get_subscription_boundaries_dict,
                timeout=settings.CACHE_DURATION_SECONDS,
            )
        else:
            boundaries_dict = self._get_subscription_boundaries_dict()

        return SubscriptionBoundaries(**boundaries_dict) if boundaries_dict else None

    def _get_subscription_boundaries_dict(self) -> dict | None:
        subscription_access = (
            ProductAccess.objects.active_for_user(self.user)
            .filter(
                product__product_type="subscription",
            )
            .only("start_date", "end_date")
            .order_by("start_date")
            .last()
        )
        if subscription_access is None:
            return None

        return {
            "start_date": subscription_access.start_date,
            "end_date": subscription_access.end_date,
        }

    def get_any_subscription_boundaries(self) -> SubscriptionBoundaries | None:
        subscription_access = ProductAccess.objects.all_subscriptions_for_user(self.user).only("start_date", "end_date").order_by("-start_date").first()

        if subscription_access is None:
            return None

        return SubscriptionBoundaries(
            start_date=subscription_access.start_date,
            end_date=subscription_access.end_date,
        )
