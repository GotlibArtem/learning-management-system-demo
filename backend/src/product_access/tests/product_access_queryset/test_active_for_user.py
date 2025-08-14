from datetime import datetime

import pytest
from django.utils import timezone

from product_access.models import ProductAccess


pytestmark = [
    pytest.mark.django_db,
]


@pytest.fixture
def ya_user(factory):
    return factory.user()


@pytest.mark.parametrize(
    ("start_date", "end_date", "expected"),
    [
        (datetime(2010, 3, 1, 0, 0, 0, 0), datetime(2010, 3, 15, 23, 59, 59, 999999), True),  # active access
        (datetime(2010, 3, 11, 0, 0, 0, 0), datetime(2010, 3, 15, 23, 59, 59, 999999), False),  # active is in the future
        (datetime(2010, 3, 8, 0, 0, 0, 0), datetime(2010, 3, 9, 23, 59, 59, 999999), False),  # expired access
        (datetime(2010, 3, 10, 0, 0, 0, 0), datetime(2010, 3, 10, 23, 59, 59, 999999), True),  # access includes start and end dates
        (datetime(2010, 3, 9, 0, 0, 0, 0), None, True),  # eternal access
        (datetime(2010, 3, 11, 0, 0, 0, 0), None, False),  # future eternal access
    ],
)
@pytest.mark.freeze_time("2010-03-10")
def test_only_active_access_is_included(user, product_access, start_date, end_date, expected):
    product_access.start_date = start_date
    product_access.end_date = end_date
    product_access.save()

    access_items = ProductAccess.objects.active_for_user(user)

    assert (product_access in access_items) is expected


def test_exclude_access_of_other_users(product_access, user, ya_user):
    product_access.setattr_and_save("user", ya_user)

    access_items = ProductAccess.objects.active_for_user(user)

    assert product_access not in access_items


def test_exclude_revoked_access(product_access, user):
    product_access.setattr_and_save("revoked_at", timezone.now())

    access_items = ProductAccess.objects.active_for_user(user)

    assert product_access not in access_items
