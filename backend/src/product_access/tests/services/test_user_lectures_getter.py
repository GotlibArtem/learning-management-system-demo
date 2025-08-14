from datetime import date

import pytest

from product_access.services import UserLecturesGetter


pytestmark = [
    pytest.mark.django_db,
    pytest.mark.usefixtures("course_version"),
    pytest.mark.usefixtures("course_plan"),
]


@pytest.fixture
def getter(user):
    return UserLecturesGetter(user=user)


@pytest.fixture
def subscription_access(product, product_access, course):
    course.setattr_and_save("is_available_by_subscription", True)
    product.setattr_and_save("product_type", "subscription")
    product_access.setattr_and_save("start_date", date(2020, 3, 1))
    return product_access


@pytest.mark.usefixtures("subscription_access")
@pytest.mark.parametrize("state", ["archived", "published"])
def test_include_lecture_if_user_has_access_to_course(getter, lecture, course_version, state):
    course_version.setattr_and_save("state", state)

    assert lecture.id in getter()


def test_exclude_lecture_if_user_has_no_access_to_course(getter, lecture):
    assert lecture.id not in getter()


@pytest.mark.freeze_time("2020-12-05")
@pytest.mark.usefixtures("subscription_access")
@pytest.mark.parametrize(
    ("scheduled_at", "expected"),
    [
        ("2020-12-04", True),
        ("2020-12-05", True),
        (None, True),
        ("2020-12-06", False),
    ],
)
def test_access_depends_on_schedule_time_when_lectures_history_is_available(getter, lecture, make_dt, scheduled_at, expected):
    lecture.setattr_and_save("scheduled_at", scheduled_at and make_dt(scheduled_at))

    assert (lecture.id in getter()) is expected


@pytest.mark.freeze_time("2020-12-05")
@pytest.mark.usefixtures("subscription_access")
@pytest.mark.parametrize(
    ("scheduled_at", "expected"),
    [
        ("2020-02-01", False),
        ("2020-03-01T12:00:00", True),
        ("2020-03-02", True),
        ("2020-12-05", True),
        ("2020-12-06", False),
        (None, True),
    ],
)
def test_access_depends_on_schedule_time_when_lectures_history_is_not_available(getter, lecture, course, scheduled_at, expected, make_dt):
    course.setattr_and_save("is_lectures_history_available", False)

    lecture.setattr_and_save("scheduled_at", scheduled_at and make_dt(scheduled_at))

    assert (lecture.id in getter()) is expected
