from datetime import date

import pytest

from product_access.services import UserCoursePlansGetter


pytestmark = [
    pytest.mark.django_db,
]


@pytest.fixture
def getter(user):
    return UserCoursePlansGetter(user=user, include_series=False)


@pytest.fixture
def course_plan_access(product_access, product, course_plan, course_version):
    product.course_versions_plans.add(course_version, through_defaults={"course_plan": course_plan})
    product.setattr_and_save("product_type", "course")
    return product_access


@pytest.fixture
def another_course(factory):
    return factory.course()


@pytest.fixture
def another_course_version(factory, another_course):
    return factory.course_version(course=another_course, state="published")


@pytest.fixture
def another_course_plan(factory, another_course_version):
    return factory.course_plan(course_version=another_course_version, default_for_version=True)


@pytest.fixture
def mock_series_access(mocker, course_series, another_course_version):
    course_series.course_versions.set([another_course_version])
    return mocker.patch("product_access.services.user_course_plans_getter.UserCourseSeriesGetter.act", return_value={course_series.id})


@pytest.fixture
def ya_user(factory):
    return factory.user()


@pytest.mark.usefixtures("course_plan_access")
def test_include_course_plan_with_access(course_plan, getter):
    assert course_plan.id in getter()


def test_exclude_course_plan_if_no_access(getter, course_plan):
    assert course_plan.id not in getter()


def test_exclude_course_plans_of_other_users(getter, course_plan_access, ya_user, course_plan):
    course_plan_access.setattr_and_save("user", ya_user)

    assert course_plan.id not in getter()


@pytest.mark.freeze_time("2010-03-10")
def test_exclude_course_plan_if_access_is_inactive(getter, course_plan_access, course_plan):
    course_plan_access.setattr_and_save("start_date", date(2020, 3, 10))

    assert course_plan.id not in getter()


@pytest.mark.usefixtures("mock_series_access", "course_plan")
def test_exclude_course_plans_from_series_optionally(getter, another_course_plan):
    assert another_course_plan.id not in getter()


@pytest.mark.usefixtures("mock_series_access", "course_plan")
def test_include_course_plans_from_series_optionally(getter, another_course_plan):
    getter.include_series = True

    assert another_course_plan.id in getter()


@pytest.mark.parametrize(
    ("state", "expected"),
    [
        ("draft", False),
        ("published", True),
        ("archived", True),
        ("closed", False),
    ],
)
@pytest.mark.usefixtures("course_plan_access")
def test_exclude_course_plans_by_version_state(getter, course_plan, state, expected):
    course_plan.course_version.setattr_and_save("state", state)

    assert (course_plan.id in getter()) is expected


@pytest.mark.usefixtures("mock_series_access")
def test_exclude_non_default_course_plan_from_series(getter, another_course_plan):
    getter.include_series = True
    another_course_plan.setattr_and_save("default_for_version", False)

    assert another_course_plan.id not in getter()
