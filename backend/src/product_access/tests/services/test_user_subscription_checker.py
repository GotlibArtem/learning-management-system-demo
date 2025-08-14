from datetime import date

import pytest

from product_access.services import UserSubscriptionChecker


pytestmark = [
    pytest.mark.django_db,
]


@pytest.fixture
def checker(user):
    return UserSubscriptionChecker(user=user)


@pytest.fixture
def ya_user(factory):
    return factory.user()


@pytest.fixture
def subscription_access(product_access, product):
    product.setattr_and_save("product_type", "subscription")
    return product_access


@pytest.mark.usefixtures("subscription_access")
def test_active_subscription_if_access_is_active(checker):
    assert checker() is True


@pytest.mark.freeze_time("2010-03-10")
def test_inactive_subscription_if_access_is_inactive(checker, subscription_access):
    subscription_access.setattr_and_save("start_date", date(2020, 3, 10))

    assert checker() is False


def test_exclude_subscription_of_other_user(checker, subscription_access, ya_user):
    subscription_access.setattr_and_save("user", ya_user)

    assert checker() is False


@pytest.mark.usefixtures("subscription_access")
def test_include_only_products_of_subscription_type(checker, product):
    product.setattr_and_save("product_type", "course")

    assert checker() is False
