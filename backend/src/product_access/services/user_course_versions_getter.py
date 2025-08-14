from dataclasses import dataclass
from uuid import UUID

from courses.models import CourseVersion
from django.conf import settings
from django.core.cache import cache
from django.db.models import Q
from django.utils.functional import cached_property

from app.services import BaseService
from product_access.models import ProductAccess
from product_access.services.user_course_series_getter import UserCourseSeriesGetter
from users.models import User


@dataclass
class UserCourseVersionsGetter(BaseService):
    """
    Return ids of courses available for user
    """

    user: User
    include_series: bool

    def act(self) -> set[UUID]:
        if settings.CACHE_ENABLED:
            return cache.get_or_set(  # type: ignore[return-value]
                f"user_course_versions_{self.user.id}_with_series_{self.include_series}",
                self.get_avaialble_course_versions,
                timeout=settings.CACHE_DURATION_SECONDS,
            )
        return self.get_avaialble_course_versions()

    def get_avaialble_course_versions(self) -> set[UUID]:
        access_items = tuple(ProductAccess.objects.active_for_user(self.user).values_list("id", flat=True))
        query = Q(products__access_items__in=access_items, state__in=["published", "archived"])
        if self.include_series:
            query |= Q(course_series__in=self.available_series)
        return set(CourseVersion.objects.filter(query).values_list("id", flat=True))

    @cached_property
    def available_series(self) -> set[UUID]:
        return UserCourseSeriesGetter(user=self.user)()
