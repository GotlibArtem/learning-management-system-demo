from dataclasses import dataclass

from django.core.cache import cache

from app.services import BaseService
from users.models import User


@dataclass
class UserProductAccessCacheInvalidator(BaseService):
    """
    Invalidate all cache keys related to user's product access.
    """

    user: User

    def act(self) -> None:
        cache_keys = [
            f"subscription_boundaries_{self.user.id}",
            f"user_course_plans_{self.user.id}_with_series_True",
            f"user_course_plans_{self.user.id}_with_series_False",
            f"user_course_series_{self.user.id}",
            f"user_course_versions_{self.user.id}_with_series_True",
            f"user_course_versions_{self.user.id}_with_series_False",
            f"user_lectures_{self.user.id}",
            f"user_recurring_subscription_checker_{self.user.id}",
            f"user_subscription_checker_{self.user.id}",
        ]

        cache.delete_many(cache_keys)
