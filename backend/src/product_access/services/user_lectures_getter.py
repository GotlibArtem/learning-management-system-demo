from dataclasses import dataclass
from uuid import UUID

from courses.models import Course, Lecture
from django.conf import settings
from django.core.cache import cache
from django.db.models import OuterRef, Q, QuerySet, Subquery
from django.utils import timezone
from django.utils.functional import cached_property

from app.services import BaseService
from product_access.services.user_courses_with_access_start_date_getter import UserCoursesWithAccessStartDateGetter
from users.models import User


@dataclass
class UserLecturesGetter(BaseService):
    user: User

    def act(self) -> set[UUID]:
        if settings.CACHE_ENABLED:
            return cache.get_or_set(  # type: ignore[return-value]
                f"user_lectures_{self.user.id}",
                self.get_avaialble_lectures,
                timeout=settings.CACHE_DURATION_SECONDS,
            )
        return self.get_avaialble_lectures()

    def get_avaialble_lectures(self) -> set[UUID]:
        return set(Lecture.objects.filter(self.allow_by_course_access_q & self.allow_by_schedule_q).values_list("id", flat=True))

    @cached_property
    def available_courses(self) -> QuerySet[Course]:
        return UserCoursesWithAccessStartDateGetter(user=self.user)()

    @property
    def allow_by_course_access_q(self) -> Q:
        return Q(courses__in=self.available_courses)

    @property
    def allow_by_schedule_q(self) -> Q:
        allow_not_scheduled = Q(scheduled_at__isnull=True)
        allow_because_lectures_history_available = Q(courses__is_lectures_history_available=True) & Q(scheduled_at__lte=timezone.now())
        allow_inside_access_boundaries = (
            Q(courses__is_lectures_history_available=False)
            & Q(scheduled_at__lte=timezone.now())
            & Q(scheduled_at__gte=Subquery(self.available_courses.filter(lectures=OuterRef("id")).values("access_start_date")[:1]))  # type: ignore[misc]
        )
        return allow_not_scheduled | allow_because_lectures_history_available | allow_inside_access_boundaries
