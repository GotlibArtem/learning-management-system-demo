from datetime import date

import pytest
from django.utils.timezone import now

from payments.models import RecurrentStatus
from product_access.services import UserRecurringSubscriptionChecker


pytestmark = [
    pytest.mark.django_db,
]


@pytest.fixture
def checker(user):
    return UserRecurringSubscriptionChecker(user=user)


@pytest.fixture
def ya_user(factory):
    return factory.user()


@pytest.fixture
def subscription_access(product_access, product):
    product.setattr_and_save("product_type", "subscription")
    return product_access


@pytest.fixture
def recurrent_subscription(user, product, recurrent):
    product.setattr_and_save("product_type", "subscription")
    recurrent.setattr_and_save("user", user)
    recurrent.setattr_and_save("product", product)
    recurrent.setattr_and_save("next_charge_date", now())

    return recurrent


def test_true_if_access_and_recurrent_are_active(checker, subscription_access, recurrent_subscription):
    assert checker() is True


def test_false_if_only_access_is_active(checker, subscription_access):
    assert checker() is False


def test_false_if_recurrent_is_inactive(checker, subscription_access, recurrent_subscription):
    recurrent_subscription.setattr_and_save("status", RecurrentStatus.CANCELLED)

    assert checker() is False


def test_false_if_recurrent_product_is_not_subscription(checker, subscription_access, recurrent_subscription, product):
    product.setattr_and_save("product_type", "course")

    assert checker() is False


@pytest.mark.freeze_time("2010-03-10")
def test_inactive_recurring_subscription_if_access_is_inactive(checker, subscription_access, recurrent_subscription):
    subscription_access.setattr_and_save("start_date", date(2020, 3, 10))

    assert checker() is False


def test_exclude_subscription_of_other_user(checker, subscription_access, recurrent_subscription, ya_user):
    subscription_access.setattr_and_save("user", ya_user)

    assert checker() is False


def test_exclude_recurrent_of_other_user(checker, subscription_access, recurrent_subscription, ya_user):
    recurrent_subscription.setattr_and_save("user", ya_user)

    assert checker() is False


@pytest.mark.usefixtures("subscription_access")
def test_include_only_products_of_subscription_type(checker, product, recurrent_subscription):
    product.setattr_and_save("product_type", "course")
    recurrent_subscription.setattr_and_save("product", product)

    assert checker() is False
