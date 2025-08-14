from dataclasses import dataclass
from uuid import UUID

from courses.models import CourseSeries
from django.conf import settings
from django.core.cache import cache

from app.services import BaseService
from product_access.models import ProductAccess
from users.models import User


@dataclass
class UserCourseSeriesGetter(BaseService):
    """
    Return list of course series ids available for user
    """

    user: User

    def act(self) -> set[UUID]:
        if settings.CACHE_ENABLED:
            return cache.get_or_set(  # type: ignore[return-value]
                f"user_course_series_{self.user.id}",
                self.get_avaialble_course_series,
                timeout=settings.CACHE_DURATION_SECONDS,
            )
        return self.get_avaialble_course_series()

    def get_avaialble_course_series(self) -> set[UUID]:
        access_items = tuple(ProductAccess.objects.active_for_user(self.user).values_list("id", flat=True))
        return set(CourseSeries.objects.filter(products__access_items__in=access_items).values_list("id", flat=True))
