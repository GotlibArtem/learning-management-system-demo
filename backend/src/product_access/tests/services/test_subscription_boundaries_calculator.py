from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from product_access.services import SubscriptionBoundariesCalculator


msk = ZoneInfo("Europe/Moscow")


pytestmark = [
    pytest.mark.django_db,
    pytest.mark.freeze_time("2024-03-01"),
]


@pytest.fixture
def calculator(user):
    return SubscriptionBoundariesCalculator(user=user)


@pytest.fixture
def subscription_access(product_access, product):
    product.setattr_and_save("product_type", "subscription")
    product_access.end_date = datetime(2025, 3, 1, 23, 59, 59, 999999, tzinfo=msk)
    product_access.start_date = datetime(2024, 2, 10, 0, 0, 0, 0, tzinfo=msk)
    product_access.save()
    return product_access


@pytest.fixture
def ya_subscription_access(factory, user):
    product = factory.product(product_type="subscription")
    return factory.product_access(
        product=product,
        user=user,
        start_date=datetime(2025, 3, 2, 0, 0, 0, 0, tzinfo=msk),
        end_date=datetime(2025, 4, 2, 23, 59, 59, 999999, tzinfo=msk),
    )


@pytest.fixture
def ya_user(factory):
    return factory.user()


@pytest.mark.usefixtures("subscription_access")
def test_return_subscription_boundaries(calculator):
    boundaries = calculator()

    assert boundaries.start_date == datetime(2024, 2, 10, 0, 0, 0, 0, tzinfo=msk)
    assert boundaries.end_date == datetime(2025, 3, 1, 23, 59, 59, 999999, tzinfo=msk)


@pytest.mark.usefixtures("subscription_access")
def test_get_boundaries_of_the_latest_subscription_1(calculator, ya_subscription_access):
    ya_subscription_access.setattr_and_save("start_date", datetime(2024, 2, 11, 0, 0, 0, 0, tzinfo=msk))

    boundaries = calculator()

    assert boundaries.start_date == datetime(2024, 2, 11, 0, 0, 0, 0, tzinfo=msk)


@pytest.mark.usefixtures("subscription_access")
def test_get_boundaries_of_the_latest_subscription_2(calculator, ya_subscription_access):
    ya_subscription_access.setattr_and_save("start_date", datetime(2024, 2, 9, 0, 0, 0, 0, tzinfo=msk))

    boundaries = calculator()

    assert boundaries.start_date == datetime(2024, 2, 10, 0, 0, 0, 0, tzinfo=msk)


@pytest.mark.usefixtures("subscription_access")
def test_exclude_subscription_of_other_users(calculator, ya_subscription_access, ya_user):
    ya_subscription_access.setattr_and_save("user", ya_user)

    boundaries = calculator()

    assert boundaries.start_date == datetime(2024, 2, 10, 0, 0, 0, 0, tzinfo=msk)


def test_none_if_user_not_subscribed(calculator):
    assert calculator() is None


def test_get_any_subscription_returns_expired(factory):
    user = factory.user()
    product = factory.product(product_type="subscription")
    factory.product_access(
        user=user,
        product=product,
        start_date=datetime(2023, 1, 1, 0, 0, 0, 0, tzinfo=msk),
        end_date=datetime(2023, 2, 1, 23, 59, 59, 999999, tzinfo=msk),
    )

    result = SubscriptionBoundariesCalculator(user=user).get_any_subscription_boundaries()

    assert result is not None
    assert result.start_date == datetime(2023, 1, 1, 0, 0, 0, 0, tzinfo=msk)
    assert result.end_date == datetime(2023, 2, 1, 23, 59, 59, 999999, tzinfo=msk)


def test_get_any_subscription_returns_latest_by_start_date(factory):
    user = factory.user()
    product = factory.product(product_type="subscription")

    factory.product_access(
        user=user,
        product=product,
        start_date=datetime(2022, 1, 1, 0, 0, 0, 0, tzinfo=msk),
        end_date=datetime(2022, 12, 31, 23, 59, 59, 999999, tzinfo=msk),
    )

    latest = factory.product_access(
        user=user,
        product=product,
        start_date=datetime(2023, 1, 1, 0, 0, 0, 0, tzinfo=msk),
        end_date=datetime(2023, 12, 31, 23, 59, 59, 999999, tzinfo=msk),
    )

    result = SubscriptionBoundariesCalculator(user=user).get_any_subscription_boundaries()

    assert result is not None
    assert result.start_date == latest.start_date
    assert result.end_date == latest.end_date


def test_get_any_subscription_returns_none_if_no_subscriptions(factory):
    user = factory.user()

    result = SubscriptionBoundariesCalculator(user=user).get_any_subscription_boundaries()

    assert result is None
