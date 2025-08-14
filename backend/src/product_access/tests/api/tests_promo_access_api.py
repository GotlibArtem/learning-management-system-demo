from contextlib import suppress
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from a12n.models import PasswordlessEmailAuthCode
from app.models import ShopDeadLetter
from product_access.models import ProductAccess


msk = ZoneInfo("Europe/Moscow")


pytestmark = [
    pytest.mark.django_db,
]


base_url = "/api/demo/promo-access/"


@pytest.fixture(autouse=True)
def adjust_settings(settings, product):
    settings.ABSOLUTE_URL = "https://the-frontend.lms.comx"
    settings.PROMO_PRODUCT_SHOP_ID = product.shop_id


@pytest.fixture
def processing_error(mocker):
    return mocker.patch(
        "product_access.services.PromoProductCheckoutProcessor.__call__",
        side_effect=Exception("unexpected error"),
    )


@pytest.fixture
def promo_data(user):
    return {
        "eventId": "7f9b8c4b-0c9b-4d0a-8f9d-111122223333",
        "eventType": "promo-access",
        "eventTime": "2030-01-01T12:34:56Z",
        "data": {
            "user": {
                "username": user.username,
            },
        },
    }


def test_access_is_granted_with_lifetime_none(as_shop_user, promo_data, product):
    product.setattr_and_save("lifetime", None)

    resp = as_shop_user.post(base_url, data=promo_data, expected_status=200)

    access = ProductAccess.objects.get()
    assert access.user.username == promo_data["data"]["user"]["username"]
    assert access.product == product
    assert access.start_date == datetime(2030, 1, 1, 15, 34, 56, tzinfo=msk)
    assert access.end_date == datetime(2030, 1, 2, 15, 34, 56, tzinfo=msk)  # default lifetime = 1 day

    assert set(resp) == {"redirectUrl"}
    assert isinstance(resp["redirectUrl"], str)


def test_access_is_granted_with_lifetime_days(as_shop_user, promo_data, product):
    product.setattr_and_save("lifetime", 2)

    as_shop_user.post(base_url, data=promo_data, expected_status=200)

    access = ProductAccess.objects.get()
    assert access.start_date == datetime(2030, 1, 1, 15, 34, 56, tzinfo=msk)
    assert access.end_date == datetime(2030, 1, 3, 15, 34, 56, tzinfo=msk)


def test_response_redirect_url_shape(as_shop_user, promo_data):
    resp = as_shop_user.post(base_url, data=promo_data, expected_status=200)

    assert set(resp) == {"redirectUrl"}
    assert isinstance(resp["redirectUrl"], str)


def test_redirect_url_contains_code_for_existent_user(as_shop_user, promo_data):
    resp = as_shop_user.post(base_url, data=promo_data, expected_status=200)
    code = PasswordlessEmailAuthCode.objects.get().code

    assert f"&code={code}" in resp["redirectUrl"]


def test_redirect_url_contains_code_for_new_user(as_shop_user, promo_data, user):
    user.delete()

    resp = as_shop_user.post(base_url, data=promo_data, expected_status=200)
    code = PasswordlessEmailAuthCode.objects.get().code

    assert f"&code={code}" in resp["redirectUrl"]


def test_400_for_invalid_event_time(as_shop_user, promo_data):
    promo_data["eventTime"] = "invalid time"

    as_shop_user.post(base_url, data=promo_data, expected_status=400)


@pytest.mark.usefixtures("processing_error")
def test_dead_letter_is_created_on_any_error(as_shop_user, promo_data):
    with suppress(Exception):
        as_shop_user.post(base_url, data=promo_data)

    letter = ShopDeadLetter.objects.get()

    assert letter.event_type == "promo-access"
    assert letter.raw_data is not None
    assert letter.details.startswith("Traceback (most recent call last)")


def test_allow_using_product_from_settings_not_payload(as_shop_user, promo_data, product):
    product.setattr_and_save("lifetime", 1)

    as_shop_user.post(base_url, data=promo_data, expected_status=200)

    access = ProductAccess.objects.get()

    assert access.product == product
    assert access.end_date == datetime(2030, 1, 2, 15, 34, 56, tzinfo=msk)
