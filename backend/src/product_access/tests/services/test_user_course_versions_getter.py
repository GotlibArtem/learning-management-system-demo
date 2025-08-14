from datetime import date

import pytest

from product_access.services import UserCourseVersionsGetter


pytestmark = [
    pytest.mark.django_db,
]


@pytest.fixture
def getter(user):
    return UserCourseVersionsGetter(user=user, include_series=False)


@pytest.fixture
def course_version_access(product_access, product, course_version, course_plan):
    product.course_versions_plans.add(course_version, through_defaults=dict(course_plan=course_plan))
    product.setattr_and_save("product_type", "course")
    return product_access


@pytest.fixture
def series_access(product_access, product, course_series):
    product.course_series.add(course_series)
    product.setattr_and_save("product_type", "course-series")
    return product_access


@pytest.fixture
def ya_user(factory):
    return factory.user()


@pytest.mark.usefixtures("course_version_access")
def test_include_course_with_access(course_version, getter):
    assert course_version.id in getter()


def test_exclude_course_if_no_access(getter, course_version):
    assert course_version.id not in getter()


def test_exclude_courses_of_other_users(getter, course_version_access, ya_user, course_version):
    course_version_access.setattr_and_save("user", ya_user)

    assert course_version.id not in getter()


@pytest.mark.freeze_time("2010-03-10")
def test_exclude_course_if_access_is_inactive(getter, course_version_access, course_version):
    course_version_access.setattr_and_save("start_date", date(2020, 3, 10))

    assert course_version.id not in getter()


@pytest.mark.usefixtures("series_access")
def test_exclude_courses_from_series_optionally(getter, course_version):
    assert course_version.id not in getter()


@pytest.mark.usefixtures("series_access")
def test_include_courses_from_series_optionally(getter, course_version):
    getter.include_series = True

    assert course_version.id in getter()


@pytest.mark.parametrize(
    ("state", "expected"),
    [
        ("draft", False),
        ("published", True),
        ("archived", True),
        ("closed", False),
    ],
)
@pytest.mark.usefixtures("course_version_access")
def test_exclude_courses_by_state(getter, course_version, state, expected):
    course_version.setattr_and_save("state", state)

    assert (course_version.id in getter()) is expected
