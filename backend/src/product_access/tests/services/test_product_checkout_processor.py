import uuid
from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from a12n.models import PasswordlessEmailAuthCode
from product_access.models import ProductAccess
from product_access.services import ProductCheckoutProcessor, ProductCheckoutProcessorException
from products.models import Product


msk = ZoneInfo("Europe/Moscow")


pytestmark = [
    pytest.mark.django_db,
]


@pytest.fixture
def event_data(user, product, make_dt):
    return {
        "event_id": str(uuid.uuid4()),
        "event_type": "order-checkedout",
        "event_time": make_dt("2030-01-01"),
        "data": {
            "order_id": str(uuid.uuid4()),
            "user": {
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
            },
            "start_date": date(2000, 1, 2),
            "end_date": date(2000, 2, 1),
            "product": {
                "lms_id": product.id,
                "shop_id": product.shop_id,
                "name": product.name,
            },
        },
    }


@pytest.fixture
def ya_event_data(product, make_dt):
    return {
        "event_id": str(uuid.uuid4()),
        "event_type": "order-checkedout",
        "event_time": make_dt("2030-01-02"),
        "data": {
            "order_id": str(uuid.uuid4()),
            "user": {
                "username": "ya-user@email.test",
                "first_name": "Yet another",
                "last_name": "User",
            },
            "start_date": date(2000, 1, 2),
            "end_date": date(2000, 2, 1),
            "product": {
                "lms_id": product.id,
                "shop_id": product.shop_id,
                "name": product.name,
            },
        },
    }


@pytest.fixture
def processor(event_data):
    return lambda event_data=event_data: ProductCheckoutProcessor(checkout_event=event_data)()


def test_product_access_is_granted(processor, event_data, user, product):
    processor()

    access = ProductAccess.objects.get()
    assert access.user == user
    assert access.product == product
    assert access.start_date == datetime(2000, 1, 2, 0, 0, tzinfo=msk)
    assert access.end_date == datetime(2000, 2, 1, 23, 59, 59, 999999, tzinfo=msk)
    assert access.order_id == event_data["data"]["order_id"]


def test_user_rhash_is_set(processor, event_data):
    event_data["data"]["user"]["rhash"] = "test_rhash"

    processor()

    user = ProductAccess.objects.get().user
    assert user.rhash == "test_rhash"


def test_user_rhash_is_updated(processor, event_data, user):
    user.setattr_and_save("rhash", "old_rhash")
    event_data["data"]["user"]["rhash"] = "new_rhash"

    processor()

    user.refresh_from_db()
    assert user.rhash == "new_rhash"


@pytest.mark.parametrize("lms_id", ["", None])
def test_product_is_created_on_empty_lms_id(processor, event_data, lms_id):
    event_data["data"]["product"] = {
        "lms_id": lms_id,
        "shop_id": "shop-id",
        "name": "Хочу все знать",
    }

    processor()

    product = ProductAccess.objects.get().product
    assert product.shop_id == "shop-id"
    assert product.name == "Хочу все знать"


def test_product_creation_is_idempotent(processor, event_data, ya_event_data):
    product_data = {
        "lms_id": "",
        "shop_id": "shop-id",
        "name": "Хочу все знать",
    }
    event_data["data"]["product"] = product_data
    ya_event_data["data"]["product"] = product_data
    processor()

    processor(ya_event_data)

    product = Product.objects.get(shop_id="shop-id")
    assert product.name == "Хочу все знать"


def test_redirect_url_for_existent_user_doesnt_contain_autologin(processor):
    redirect_url = processor()

    assert "&code=" not in redirect_url


def test_redirect_url_for_new_user_contains_autologin(processor, user):
    user.delete()

    redirect_url = processor()

    code = PasswordlessEmailAuthCode.objects.get().code
    assert f"&code={code}" in redirect_url


def test_error_if_product_do_not_exist(processor, product):
    product.delete()

    with pytest.raises(ProductCheckoutProcessorException):
        processor()
