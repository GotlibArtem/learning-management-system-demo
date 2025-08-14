import pytest

from payments.services.tinkoff.tinkoff_recurring_charge import TinkoffRecurringCharge, TinkoffRecurringChargeException


pytestmark = [
    pytest.mark.django_db,
]


def test_successful_charge(factory):
    user = factory.user()
    product = factory.product()
    payment_instrument = factory.payment_instrument(user=user, rebill_id="rebill-123")
    recurrent = factory.recurrent(user=user, product=product, payment_instrument=payment_instrument)
    result = TinkoffRecurringCharge(recurrent=recurrent, payment_id="13660")()

    assert result["Success"] is True
    assert result["PaymentId"] == "13660"
    assert result["TerminalKey"] == "TinkoffBankTest"
    assert result["Status"] == "CONFIRMED"
    assert result["ErrorCode"] == "0"
    assert result["Amount"] == 100000
    assert result["OrderId"] == "21050"


def test_missing_rebill_id_raises(factory):
    user = factory.user()
    product = factory.product()
    payment_instrument = factory.payment_instrument(user=user, rebill_id="")
    recurrent = factory.recurrent(user=user, product=product, payment_instrument=payment_instrument)
    service = TinkoffRecurringCharge(recurrent=recurrent, payment_id="13660")

    with pytest.raises(TinkoffRecurringChargeException, match="Missing RebillId"):
        service()


def test_inactive_recurrent_raises(factory):
    user = factory.user()
    product = factory.product()
    payment_instrument = factory.payment_instrument(user=user, rebill_id="rebill-123")
    recurrent = factory.recurrent(user=user, product=product, payment_instrument=payment_instrument, status="INACTIVE")
    service = TinkoffRecurringCharge(recurrent=recurrent, payment_id="13660")

    with pytest.raises(TinkoffRecurringChargeException, match="Recurrent is not active"):
        service.validate_recurrent_status()


def test_payload_structure(factory):
    user = factory.user()
    product = factory.product()
    payment_instrument = factory.payment_instrument(user=user, rebill_id="rebill-123")
    recurrent = factory.recurrent(user=user, product=product, payment_instrument=payment_instrument)
    service = TinkoffRecurringCharge(recurrent=recurrent, payment_id="13660")
    payload = service.payload

    assert payload["PaymentId"] == "13660"
    assert payload["RebillId"] == "rebill-123"
    assert payload["SendEmail"] is True
    assert payload["InfoEmail"] == user.username


def test_charge_exception_logging(factory, monkeypatch):
    user = factory.user()
    product = factory.product()
    payment_instrument = factory.payment_instrument(user=user, rebill_id="rebill-123")
    recurrent = factory.recurrent(user=user, product=product, payment_instrument=payment_instrument)
    service = TinkoffRecurringCharge(recurrent=recurrent, payment_id="13660")

    monkeypatch.setattr(service, "post_tinkoff_charge", lambda payload: (_ for _ in ()).throw(TinkoffRecurringChargeException("fail")))

    with pytest.raises(TinkoffRecurringChargeException):
        service()
