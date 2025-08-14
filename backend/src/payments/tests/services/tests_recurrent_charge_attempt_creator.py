from decimal import Decimal

import pytest

from payments.models import RecurrentChargeAttempt, RecurrentChargeStatus
from payments.services.recurrent_charge_attempt_creator import RecurrentChargeAttemptCreator


pytestmark = [
    pytest.mark.django_db,
]


def test_charge_attempt_is_created(factory):
    user = factory.user()
    product = factory.product()
    payment_instrument = factory.payment_instrument(user=user)
    recurrent = factory.recurrent(user=user, product=product, payment_instrument=payment_instrument)
    payment = factory.payment(user=user, product=product, payment_instrument=payment_instrument)
    provider_response = {"ok": True, "code": "200"}
    attempt = RecurrentChargeAttemptCreator(
        recurrent=recurrent,
        amount=Decimal("99.99"),
        payment=payment,
        provider_response=provider_response,
        status=RecurrentChargeStatus.SUCCESS,
        currency="RUB",
        error_code="",
        error_message="",
        external_payment_id="ext-rca-001",
    )()

    assert RecurrentChargeAttempt.objects.count() == 1
    assert attempt.recurrent == recurrent
    assert attempt.payment == payment
    assert attempt.status == RecurrentChargeStatus.SUCCESS
    assert attempt.amount == Decimal("99.99")
    assert attempt.currency == "RUB"
    assert attempt.provider_response == provider_response
    assert attempt.external_payment_id == "ext-rca-001"
    assert attempt.error_code == ""
    assert attempt.error_message == ""
    assert attempt.created is not None

    recurrent.refresh_from_db()
    assert recurrent.last_attempt_charge_date.date() == attempt.created.date()
    assert recurrent.last_attempt_charge_status == RecurrentChargeStatus.SUCCESS


def test_charge_attempt_defaults(factory):
    user = factory.user()
    product = factory.product()
    payment_instrument = factory.payment_instrument(user=user)
    recurrent = factory.recurrent(user=user, product=product, payment_instrument=payment_instrument)
    provider_response = {"ok": False, "error": "timeout"}
    attempt = RecurrentChargeAttemptCreator(
        recurrent=recurrent,
        amount=Decimal("50.00"),
        provider_response=provider_response,
    )()

    assert attempt.status == RecurrentChargeStatus.SUCCESS
    assert attempt.currency == "rub"
    assert attempt.error_code == ""
    assert attempt.error_message == ""
    assert attempt.external_payment_id == ""
    assert attempt.provider_response == provider_response
    assert attempt.payment is None

    recurrent.refresh_from_db()

    assert recurrent.last_attempt_charge_status == RecurrentChargeStatus.SUCCESS


def test_charge_attempt_error_fields(factory):
    user = factory.user()
    product = factory.product()
    payment_instrument = factory.payment_instrument(user=user)
    recurrent = factory.recurrent(user=user, product=product, payment_instrument=payment_instrument)
    provider_response = {"ok": False, "error": "declined"}
    attempt = RecurrentChargeAttemptCreator(
        recurrent=recurrent,
        amount=Decimal("10.00"),
        provider_response=provider_response,
        status=RecurrentChargeStatus.FAIL,
        error_code="DECLINED",
        error_message="Card declined",
    )()

    assert attempt.status == RecurrentChargeStatus.FAIL
    assert attempt.error_code == "DECLINED"
    assert attempt.error_message == "Card declined"
    assert attempt.provider_response == provider_response

    recurrent.refresh_from_db()
    assert recurrent.last_attempt_charge_status == RecurrentChargeStatus.FAIL


def test_charge_attempt_missing_required(factory):
    user = factory.user()
    product = factory.product()
    payment_instrument = factory.payment_instrument(user=user)
    recurrent = factory.recurrent(user=user, product=product, payment_instrument=payment_instrument)

    with pytest.raises(TypeError):
        RecurrentChargeAttemptCreator(recurrent=recurrent)()
