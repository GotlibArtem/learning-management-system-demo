import uuid
from datetime import timedelta
from zoneinfo import ZoneInfo

import pytest
from django.conf import settings
from django.utils import timezone

from a12n.models import PasswordlessEmailAuthCode
from product_access.models import ProductAccess
from product_access.services import PromoProductCheckoutProcessor, PromoProductCheckoutProcessorException
from products.models import Product


msk = ZoneInfo("Europe/Moscow")


pytestmark = [
    pytest.mark.django_db,
]


@pytest.fixture
def event_data(user, product, make_dt):
    settings.PROMO_PRODUCT_SHOP_ID = product.shop_id

    return {
        "event_id": str(uuid.uuid4()),
        "event_type": "promo-24h-access",
        "event_time": make_dt("2030-01-01T12:34:56Z"),
        "data": {
            "user": {
                "username": user.username,
            },
        },
    }


@pytest.fixture
def new_user_event_data(product, make_dt):
    settings.PROMO_PRODUCT_SHOP_ID = product.shop_id

    return {
        "event_id": str(uuid.uuid4()),
        "event_type": "promo-24h-access",
        "event_time": make_dt("2030-01-02T18:30:00Z"),
        "data": {
            "user": {
                "username": "new-user@email.test",
            },
        },
    }


@pytest.fixture
def processor():
    return lambda payload: PromoProductCheckoutProcessor(checkout_event=payload)()


def test_access_granted_with_lifetime_none(processor, event_data, product):
    product.setattr_and_save("lifetime", None)

    redirect_url = processor(event_data)

    access = ProductAccess.objects.get()
    assert access.user.username == event_data["data"]["user"]["username"]
    assert access.product == product
    assert access.start_date == event_data["event_time"]
    assert access.end_date == event_data["event_time"] + timedelta(days=1)  # default lifetime = 1 day

    assert isinstance(redirect_url, str)
    assert redirect_url


def test_access_granted_with_lifetime_days(processor, event_data, product):
    product.setattr_and_save("lifetime", 1)

    processor(event_data)

    access = ProductAccess.objects.get()
    assert access.start_date == event_data["event_time"]
    assert access.end_date == event_data["event_time"] + timedelta(days=1)


def test_order_id_is_promo_event_based(processor, event_data):
    processor(event_data)

    access = ProductAccess.objects.get()
    assert access.order_id == f"promo-{event_data['event_id']}"


def test_idempotent_on_same_event(processor, event_data):
    processor(event_data)
    processor(event_data)

    assert ProductAccess.objects.count() == 1


def test_redirect_url_for_existent_user_has_code(processor, event_data):
    redirect_url = processor(event_data)
    code = PasswordlessEmailAuthCode.objects.get().code

    assert f"&code={code}" in redirect_url


def test_redirect_url_for_new_user_contains_code(processor, new_user_event_data):
    redirect_url = processor(new_user_event_data)
    code = PasswordlessEmailAuthCode.objects.get().code

    assert f"&code={code}" in redirect_url


def test_fails_if_user_has_active_subscription(processor, event_data, user):
    sub_product = Product.objects.create(
        name="Any subscription",
        product_type="subscription",
        shop_id="sub-shop",
    )

    now = timezone.now()
    ProductAccess.objects.create(
        product=sub_product,
        user=user,
        start_date=now - timedelta(days=1),
        end_date=None,
        order_id="sub-active",
        granted_at=now - timedelta(days=1),
        revoked_at=None,
    )

    with pytest.raises(PromoProductCheckoutProcessorException):
        processor(event_data)

    assert ProductAccess.objects.filter(order_id__startswith="promo-").count() == 0


def test_error_if_promo_product_not_found(processor, event_data):
    settings.PROMO_PRODUCT_SHOP_ID = "unknown-shop-id"

    with pytest.raises(PromoProductCheckoutProcessorException):
        processor(event_data)


def test_uses_product_from_settings_not_payload(processor, event_data, product):
    product.setattr_and_save("lifetime", 2)

    assert "product" not in event_data["data"]

    processor(event_data)

    access = ProductAccess.objects.get()
    assert access.product == product
    assert access.end_date == event_data["event_time"] + timedelta(days=2)
