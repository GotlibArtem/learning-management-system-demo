from contextlib import suppress
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from app.models import ShopDeadLetter
from product_access.models import ProductAccess
from products.models import Product


msk = ZoneInfo("Europe/Moscow")


pytestmark = [
    pytest.mark.django_db,
]


base_url = "/api/demo/order-checkout/"


@pytest.fixture(autouse=True)
def adjust_settings(settings):
    settings.ABSOLUTE_URL = "https://the-frontend.lms.comx"


@pytest.fixture
def processing_error(mocker):
    return mocker.patch(
        "product_access.services.ProductCheckoutProcessor.__call__",
        side_effect=Exception("unexpected error"),
    )


def test_access_is_granted(as_shop_user, checkout_data, product, user):
    as_shop_user.post(base_url, data=checkout_data, expected_status=200)

    access = ProductAccess.objects.get()
    assert access.user == user
    assert access.product == product

    assert access.start_date == datetime(2000, 1, 1, 0, 0, 0, 0, tzinfo=msk)
    assert access.end_date == datetime(2000, 2, 1, 23, 59, 59, 999999, tzinfo=msk)
    assert access.order_id == checkout_data["data"]["orderId"]


def test_response(as_shop_user, checkout_data, user):
    user.setattr_and_save("username", "some@email.test")

    response = as_shop_user.post(base_url, data=checkout_data, expected_status=200)

    assert response["redirectUrl"].startswith("https://the-frontend.lms.comx/order-checkedout?")
    assert set(response) == {"redirectUrl"}


def test_redirect_url_doesnt_contain_code_for_existent_user(as_shop_user, checkout_data):
    response = as_shop_user.post(base_url, data=checkout_data, expected_status=200)

    assert "&code=" not in response["redirectUrl"]


def test_400_for_invalid_data(as_shop_user, checkout_data):
    checkout_data["eventTime"] = "invalid time"

    as_shop_user.post(base_url, data=checkout_data, expected_status=400)


@pytest.mark.parametrize("empty_value", ["", None])
def test_name_can_be_empty(as_shop_user, checkout_data, empty_value):
    checkout_data["data"]["user"].update(first_name=empty_value, last_name=empty_value)

    as_shop_user.post(base_url, data=checkout_data, expected_status=200)

    user = ProductAccess.objects.get().user
    assert user.first_name == ""
    assert user.last_name == ""


@pytest.mark.parametrize("empty_value", [None, ""])
def test_create_product_on_empty_lms_id(as_shop_user, checkout_data, product, empty_value):
    product.delete()
    checkout_data["data"]["product"]["lmsId"] = empty_value

    as_shop_user.post(base_url, data=checkout_data, expected_status=200)

    product = Product.objects.get()
    assert product.shop_id == checkout_data["data"]["product"]["shopId"]
    assert product.name == checkout_data["data"]["product"]["name"]


def test_allow_empty_end_date(as_shop_user, checkout_data):
    checkout_data["data"]["endDate"] = None

    as_shop_user.post(base_url, data=checkout_data, expected_status=200)

    product_access = ProductAccess.objects.get()
    assert product_access.end_date is None


@pytest.mark.usefixtures("processing_error")
def test_dead_letter_is_created_on_any_error(as_shop_user, checkout_data):
    with suppress(Exception):
        as_shop_user.post(base_url, data=checkout_data)

    letter = ShopDeadLetter.objects.get()
    assert letter.event_type == "order-checkedout"
    assert letter.raw_data is not None
    assert letter.details.startswith("Traceback (most recent call last)")
