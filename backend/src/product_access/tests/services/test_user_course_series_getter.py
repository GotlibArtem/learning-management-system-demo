from datetime import date

import pytest

from product_access.services import UserCourseSeriesGetter


pytestmark = [
    pytest.mark.django_db,
]


@pytest.fixture
def getter(user):
    return UserCourseSeriesGetter(user=user)


@pytest.fixture
def series_access(product_access, product, course_series, course):
    course.setattr_and_save("is_available_by_subscription", False)
    product.course_series.add(course_series)
    product.setattr_and_save("product_type", "course-series")
    return product_access


@pytest.fixture
def ya_user(factory):
    return factory.user()


@pytest.mark.usefixtures("series_access")
def test_include_series_with_access(getter, course_series):
    assert course_series.id in getter()


def test_exclude_series_if_no_access(getter, course_series):
    assert course_series.id not in getter()


def test_exclude_series_of_other_users(getter, series_access, ya_user, course_series):
    series_access.setattr_and_save("user", ya_user)

    assert course_series.id not in getter()


@pytest.mark.freeze_time("2010-03-10")
def test_exclude_series_if_access_is_inactive(getter, series_access, course_series):
    series_access.setattr_and_save("start_date", date(2020, 3, 10))

    assert course_series.id not in getter()
