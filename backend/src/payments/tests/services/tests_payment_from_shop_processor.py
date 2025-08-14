import pytest

from payments.models import Payment, PaymentInstrument, RecurrentChargeAttempt, RecurrentChargeStatus
from payments.services import PaymentFromShopProcessor, PaymentFromShopProcessorException


pytestmark = [
    pytest.mark.django_db,
]


def test_payment_is_created(payment_data):
    payment = PaymentFromShopProcessor(payment_data)()

    assert Payment.objects.count() == 1
    assert payment.external_payment_id == payment_data["payment_id"]
    assert payment.user.username == payment_data["user"]["email"]
    assert payment.user.phone == payment_data["user"]["phone"]
    assert payment.product.id == payment_data["product"]["lms_id"]
    assert payment.status == payment_data["status"]


def test_idempotency_of_payment_creation(payment_data):
    PaymentFromShopProcessor(payment_data)()
    PaymentFromShopProcessor(payment_data)()

    assert Payment.objects.count() == 1


def test_optional_fields_defaults(payment_data):
    for key in ("discount_price", "bonus_applied", "promo_code", "provider_response"):
        payment_data.pop(key, None)

    payment = PaymentFromShopProcessor(payment_data)()

    assert payment.discount_price == 0
    assert payment.bonus_applied == 0
    assert payment.promo_code == ""
    assert payment.provider_response is None


def test_create_recurrent_and_instrument_and_charge_attempt(payment_data, recurrent_data):
    payment_data["recurrent"] = recurrent_data.copy()

    payment = PaymentFromShopProcessor(payment_data)()
    recurrent = payment.recurrent

    assert recurrent is not None
    assert recurrent.status == recurrent_data["status"]
    assert recurrent.amount == recurrent_data["amount"]

    assert PaymentInstrument.objects.count() == 1

    instrument = PaymentInstrument.objects.first()

    assert instrument.rebill_id == recurrent_data["attempts_charge"][0]["rebill_id"]

    attempt = RecurrentChargeAttempt.objects.first()

    assert attempt is not None
    assert attempt.payment == payment
    assert attempt.recurrent == recurrent
    assert attempt.status == RecurrentChargeStatus.SUCCESS
    assert attempt.external_payment_id == recurrent_data["attempts_charge"][0]["payment_id"]


def test_recurrent_is_updated(payment_data, recurrent_data):
    payment_data["recurrent"] = recurrent_data.copy()
    first = PaymentFromShopProcessor(payment_data)()
    recurrent = first.recurrent

    payment_data["recurrent"]["status"] = "CANCELLED"
    payment_data["recurrent"]["amount"] = 150

    second = PaymentFromShopProcessor(payment_data)()
    recurrent.refresh_from_db()

    assert recurrent.status == "CANCELLED"
    assert recurrent.amount == 150
    assert second.recurrent.id == recurrent.id


def test_recurrent_not_created_if_not_present(payment_data):
    payment = PaymentFromShopProcessor(payment_data)()

    assert payment.recurrent is None
    assert PaymentInstrument.objects.count() == 0
    assert RecurrentChargeAttempt.objects.count() == 0


def test_exception_if_product_does_not_exist(payment_data):
    payment_data["product"]["lms_id"] = 999999
    processor = PaymentFromShopProcessor(payment_data)

    with pytest.raises(PaymentFromShopProcessorException):
        processor()
