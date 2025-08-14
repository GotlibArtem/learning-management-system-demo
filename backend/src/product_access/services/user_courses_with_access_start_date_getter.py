from dataclasses import dataclass
from datetime import date

from courses.models import Course
from django.db.models import DateField, OuterRef, Q, QuerySet, Subquery, Value
from django.db.models.functions import Coalesce
from django.utils.functional import cached_property

from app.services import BaseService
from product_access.models import ProductAccess
from product_access.services.subscription_boundaries_calculator import SubscriptionBoundariesCalculator
from users.models import User


@dataclass
class UserCoursesWithAccessStartDateGetter(BaseService):
    """
    Returns user courses with access start date
    """

    user: User

    def act(self) -> QuerySet[Course]:
        direct_access_start_date_subquery = (
            ProductAccess.objects.filter(user=self.user)
            .filter(Q(product__course_versions_plans__course=OuterRef("id")) | Q(product__course_series__course_versions__course=OuterRef("id")))
            .order_by("start_date")
            .values("start_date")[:1]
        )
        return Course.objects.annotate(
            access_start_date=Coalesce(
                Subquery(direct_access_start_date_subquery),
                Value(self.subscription_start_date, output_field=DateField()),
            ),
        ).available_for_user(self.user)

    @cached_property
    def subscription_start_date(self) -> date | None:
        boundaries = SubscriptionBoundariesCalculator(user=self.user)()
        return boundaries.start_date if boundaries else None
