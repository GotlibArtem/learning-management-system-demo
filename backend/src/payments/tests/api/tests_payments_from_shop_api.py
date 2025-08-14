from contextlib import suppress

import pytest

from app.models import ShopDeadLetter
from payments.models import Payment, PaymentInstrument, RecurrentChargeAttempt


pytestmark = [
    pytest.mark.django_db,
]


base_url = "/api/demo/payments/from-shop/"


@pytest.fixture(autouse=True)
def adjust_settings(settings):
    settings.ABSOLUTE_URL = "https://the-frontend.lms.comx"


@pytest.fixture
def processing_error(mocker):
    return mocker.patch(
        "payments.services.PaymentFromShopProcessor.__call__",
        side_effect=Exception("unexpected error"),
    )


def test_payment_is_created(as_shop_user, payment_data):
    as_shop_user.post(base_url, data=payment_data, expected_status=201)

    payment = Payment.objects.get(external_payment_id=payment_data["payment_id"])

    assert payment.user.username == payment_data["user"]["email"]
    assert payment.user.phone == payment_data["user"]["phone"]
    assert payment.product.shop_id == payment_data["product"]["shop_id"]
    assert str(payment.status) == payment_data["status"]


def test_recurrent_is_created_when_present(as_shop_user, payment_data, recurrent_data):
    payment_data["recurrent"] = recurrent_data.copy()
    as_shop_user.post(base_url, data=payment_data, expected_status=201)

    payment = Payment.objects.get(external_payment_id=payment_data["payment_id"])

    assert payment.recurrent is not None
    assert payment.recurrent.status == recurrent_data["status"]


def test_idempotency_of_payment_creation(as_shop_user, payment_data):
    as_shop_user.post(base_url, data=payment_data, expected_status=201)
    as_shop_user.post(base_url, data=payment_data, expected_status=201)

    assert Payment.objects.filter(external_payment_id=payment_data["payment_id"]).count() == 1


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("promo_code", None),
        ("promo_code", ""),
        ("bonus_applied", None),
        ("discount_price", None),
    ],
)
def test_optional_fields_are_accepted(as_shop_user, payment_data, field, value):
    payment_data[field] = value
    as_shop_user.post(base_url, data=payment_data, expected_status=201)

    payment = Payment.objects.get(external_payment_id=payment_data["payment_id"])

    assert payment is not None


def test_400_if_required_fields_missing(as_shop_user, payment_data):
    del payment_data["payment_id"]

    as_shop_user.post(base_url, data=payment_data, expected_status=400)


def test_product_created_if_empty_lms_id(as_shop_user, payment_data):
    payment_data["product"]["lms_id"] = ""
    as_shop_user.post(base_url, data=payment_data, expected_status=201)

    payment = Payment.objects.get(external_payment_id=payment_data["payment_id"])

    assert payment.product.shop_id == payment_data["product"]["shop_id"]


def test_empty_names_are_allowed(as_shop_user, payment_data):
    payment_data["user"]["first_name"] = ""
    payment_data["user"]["last_name"] = ""
    as_shop_user.post(base_url, data=payment_data, expected_status=201)

    payment = Payment.objects.get(external_payment_id=payment_data["payment_id"])

    assert payment.user.first_name == ""
    assert payment.user.last_name == ""


def test_instrument_and_attempt_are_created(as_shop_user, payment_data, recurrent_data):
    payment_data["recurrent"] = recurrent_data
    as_shop_user.post(base_url, data=payment_data, expected_status=201)

    assert PaymentInstrument.objects.count() == 1
    assert RecurrentChargeAttempt.objects.count() == 1


def test_recurrent_is_updated_if_exists(as_shop_user, payment_data, recurrent_data):
    payment_data["recurrent"] = recurrent_data
    as_shop_user.post(base_url, data=payment_data, expected_status=201)

    payment_data["recurrent"]["status"] = "CANCELLED"
    payment_data["recurrent"]["amount"] = 150
    as_shop_user.post(base_url, data=payment_data, expected_status=201)

    payment = Payment.objects.get(external_payment_id=payment_data["payment_id"])
    recurrent = payment.recurrent

    assert recurrent.status == "CANCELLED"
    assert recurrent.amount == 150


def test_no_recurrent_created_if_missing(as_shop_user, payment_data):
    as_shop_user.post(base_url, data=payment_data, expected_status=201)

    payment = Payment.objects.get(external_payment_id=payment_data["payment_id"])

    assert payment.recurrent is None
    assert PaymentInstrument.objects.count() == 0
    assert RecurrentChargeAttempt.objects.count() == 0


def test_invalid_data_returns_400(as_shop_user):
    as_shop_user.post(base_url, data={}, expected_status=400)


@pytest.mark.usefixtures("processing_error")
def test_dead_letter_is_created_on_any_error(as_shop_user, payment_data):
    with suppress(Exception):
        as_shop_user.post(base_url, data=payment_data)

    letter = ShopDeadLetter.objects.get()

    assert letter.event_type == "incoming-payment-from-shop"
    assert letter.raw_data is not None
    assert letter.details.startswith("Traceback (most recent call last)")
