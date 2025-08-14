from datetime import datetime

import pytest
from django.conf import settings
from django.utils.timezone import now


pytestmark = [pytest.mark.django_db]

base_url = "/api/demo/users/me/"


@pytest.fixture
def subscription(product_access, product):
    product.setattr_and_save("product_type", "subscription")
    product_access.start_date = datetime(2000, 1, 1, 0, 0, 0, 0)
    product_access.end_date = datetime(2101, 3, 2, 23, 59, 59, 999999)
    product_access.save()
    return product_access


@pytest.fixture
def recurring_subscription(product_access, product, recurrent):
    product.setattr_and_save("product_type", "subscription")
    product.setattr_and_save("shop_id", settings.RECURRING_SUBSCRIPTION_SHOP_ID)
    product_access.start_date = datetime(2000, 1, 1, 0, 0, 0, 0)
    product_access.end_date = datetime(2101, 3, 2, 23, 59, 59, 999999)
    product_access.save()
    recurrent.setattr_and_save("user", product_access.user)
    recurrent.setattr_and_save("product", product)
    recurrent.setattr_and_save("next_charge_date", now())
    return product_access


def test_response(as_user, user):
    response = as_user.get(base_url)

    assert response["id"] == str(user.pk)
    assert response["username"] == user.username
    assert response["firstName"] == user.first_name
    assert response["lastName"] == user.last_name
    assert response["birthdate"] == user.birthdate
    assert response["avatarSlug"] == user.avatar_slug
    assert response["remoteAddr"] == "127.0.0.1"
    assert response["hasAcceptedDataConsent"] is None
    assert response["hasRecurringSubscription"] is False
    assert response["subscriptionStartDate"] is None
    assert response["subscriptionEndDate"] is None
    assert set(response) == {
        "id",
        "username",
        "firstName",
        "lastName",
        "birthdate",
        "avatarSlug",
        "remoteAddr",
        "hasAcceptedDataConsent",
        "hasRecurringSubscription",
        "subscriptionStartDate",
        "subscriptionEndDate",
        "rhash",
    }


@pytest.mark.usefixtures("subscription")
def test_response_with_subscription(as_user):
    response = as_user.get(base_url)

    assert response["subscriptionStartDate"] == "2000-01-01T00:00:00+03:00"
    assert response["subscriptionEndDate"] == "2101-03-02T23:59:59.999999+03:00"
    assert response["hasRecurringSubscription"] is False


@pytest.mark.usefixtures("recurring_subscription")
def test_response_with_recurring_subscription(as_user):
    response = as_user.get(base_url)

    assert response["subscriptionStartDate"] == "2000-01-01T00:00:00+03:00"
    assert response["subscriptionEndDate"] == "2101-03-02T23:59:59.999999+03:00"
    assert response["hasRecurringSubscription"] is True


def test_anon(as_anon):
    response = as_anon.get(base_url, as_response=True)

    assert response.status_code == 401
