import pytest
import requests

from payments.models import PaymentStatus, RecurrentChargeStatus
from payments.services.tinkoff.tinkoff_recurring_charge_processor import TinkoffRecurringChargeProcessor, TinkoffRecurringChargeProcessorException


pytestmark = [
    pytest.mark.django_db,
]


def make_recurrent(factory, status="ACTIVE", amount=1000, payment_instrument_kwargs=None):
    user = factory.user()
    product = factory.product()
    payment_instrument = factory.payment_instrument(user=user, **(payment_instrument_kwargs or {}))
    return factory.recurrent(user=user, product=product, payment_instrument=payment_instrument, status=status, amount=amount)


def test_successful_charge_processor(factory):
    recurrent = make_recurrent(factory, amount=100000)
    payment, charge_attempt = TinkoffRecurringChargeProcessor(recurrent=recurrent)()

    assert payment is not None
    assert charge_attempt is not None
    assert payment.status == PaymentStatus.PAID
    assert payment.amount == 1000
    assert payment.external_payment_id == "13660"
    assert charge_attempt.status == RecurrentChargeStatus.SUCCESS
    assert charge_attempt.amount == 1000
    assert charge_attempt.external_payment_id == "13660"
    assert charge_attempt.provider_response["Status"] == "CONFIRMED"


def test_charge_processor_no_payment_on_fail(factory):
    recurrent = make_recurrent(factory, amount=1000)

    def mock_post(url, *a, **kw):
        if url.endswith("/Charge"):

            class FailResponse:
                def json(self):
                    return {"Success": False, "Status": "FAILED", "PaymentId": "99999", "Amount": 100000}

            return FailResponse()

        class SuccessResponse:
            def json(self):
                return {
                    "Success": True,
                    "ErrorCode": "0",
                    "TerminalKey": "TinkoffBankTest",
                    "Status": "NEW",
                    "PaymentId": "3093639567",
                    "OrderId": "21090",
                    "Amount": 100000,
                    "PaymentURL": "https://securepay.tinkoff.ru/new/fU1ppgqa",
                }

        return SuccessResponse()

    orig_post = requests.post
    requests.post = mock_post
    try:
        payment, charge_attempt = TinkoffRecurringChargeProcessor(recurrent=recurrent)()

        assert payment is None
        assert charge_attempt is not None
        assert charge_attempt.status == RecurrentChargeStatus.FAIL
        assert charge_attempt.external_payment_id == "99999"
    finally:
        requests.post = orig_post


def test_charge_processor_handles_exceptions(factory, monkeypatch):
    recurrent = make_recurrent(factory)
    monkeypatch.setattr(
        "payments.services.tinkoff.TinkoffRecurringInit.act",
        lambda self: (_ for _ in ()).throw(TinkoffRecurringChargeProcessorException("Init fail")),
    )
    processor = TinkoffRecurringChargeProcessor(recurrent=recurrent)

    with pytest.raises(TinkoffRecurringChargeProcessorException, match="Init fail"):
        processor()


def test_charge_processor_payment_fields(factory):
    recurrent = make_recurrent(factory)
    payment, _ = TinkoffRecurringChargeProcessor(recurrent=recurrent)()

    assert payment is not None
    assert payment.amount == 1000
    assert payment.status == PaymentStatus.PAID
    assert payment.provider_response["PaymentId"] == "13660"
    assert payment.provider_response["Status"] == "CONFIRMED"


def test_charge_processor_attempt_fields(factory):
    recurrent = make_recurrent(factory)
    _, charge_attempt = TinkoffRecurringChargeProcessor(recurrent=recurrent)()

    assert charge_attempt is not None
    assert charge_attempt.amount == 1000
    assert charge_attempt.status == RecurrentChargeStatus.SUCCESS
    assert charge_attempt.provider_response["PaymentId"] == "13660"
    assert charge_attempt.provider_response["Status"] == "CONFIRMED"
