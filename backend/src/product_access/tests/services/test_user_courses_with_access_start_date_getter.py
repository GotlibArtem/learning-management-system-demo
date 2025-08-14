from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from django.utils import timezone

from product_access.services import UserCoursesWithAccessStartDateGetter


msk = ZoneInfo("Europe/Moscow")


pytestmark = [
    pytest.mark.django_db,
    pytest.mark.usefixtures("course_version"),
]


def msk_to_utc(y, m, d):
    dt_msk = datetime(y, m, d, 0, 0, tzinfo=msk)
    return dt_msk.astimezone(ZoneInfo("UTC"))


def assert_msk(actual_dt, y, m, d, hh=0, mm=0, ss=0, us=0):
    actual = timezone.localtime(actual_dt, msk)
    expected = datetime(y, m, d, hh, mm, ss, us, tzinfo=msk)
    assert actual == expected


@pytest.fixture
def getter(user):
    return UserCoursesWithAccessStartDateGetter(user=user)


@pytest.fixture
def direct_access(product, product_access, course_version, course_plan):
    product.course_versions_plans.add(course_version, through_defaults=dict(course_plan=course_plan))
    product.setattr_and_save("product_type", "course")
    product_access.setattr_and_save("start_date", msk_to_utc(2020, 3, 1))
    return product_access


@pytest.fixture
def subscription_access(product, product_access, course):
    course.setattr_and_save("is_available_by_subscription", True)
    product.setattr_and_save("product_type", "subscription")
    product_access.setattr_and_save("start_date", msk_to_utc(2020, 3, 1))
    return product_access


@pytest.fixture
def ya_direct_access(factory, user):
    product = factory.product()
    course_version = factory.course_version(state="published")
    product.course_versions_plans.add(course_version, through_defaults=dict(course_plan=factory.course_plan(course_version=course_version)))
    return factory.product_access(product=product, user=user, start_date=msk_to_utc(2019, 3, 1))


@pytest.fixture
def ya_user_direct_access(factory, product, course_version, course_plan):
    product.course_versions_plans.add(course_version, through_defaults=dict(course_plan=course_plan))
    product.setattr_and_save("product_type", "course")
    return factory.product_access(product=product, start_date=msk_to_utc(2019, 3, 1), user=factory.user())


@pytest.mark.usefixtures("direct_access")
def test_annotate_with_access_start_date(getter):
    got_course = getter().get()

    assert_msk(got_course.access_start_date, 2020, 3, 1, 0, 0, 0)


@pytest.mark.usefixtures("direct_access", "ya_user_direct_access")
def test_exclude_access_of_other_users_during_start_date_calculation(getter):
    got_course = getter().get()

    assert_msk(got_course.access_start_date, 2020, 3, 1, 0, 0, 0)


@pytest.mark.usefixtures("direct_access", "ya_direct_access")
def test_exclude_access_to_other_course_during_start_date_calculation(getter, course):
    got_course = getter().get(id=course.id)

    assert_msk(got_course.access_start_date, 2020, 3, 1, 0, 0, 0)


@pytest.mark.usefixtures("direct_access")
def test_include_course_access_through_course_series(getter, product, course_series):
    product.course_versions_plans.clear()
    product.course_series.add(course_series)
    product.setattr_and_save("product_type", "course-series")

    got_course = getter().get()

    assert_msk(got_course.access_start_date, 2020, 3, 1, 0, 0, 0)


@pytest.mark.usefixtures("subscription_access")
def test_use_subscription_start_date_for_subscription_access(getter):
    got_course = getter().get()

    assert_msk(got_course.access_start_date, 2020, 3, 1, 3, 0, 0)


@pytest.mark.usefixtures("subscription_access")
def test_exclude_course_without_access(getter, course):
    course.setattr_and_save("is_available_by_subscription", False)

    assert course not in getter()
