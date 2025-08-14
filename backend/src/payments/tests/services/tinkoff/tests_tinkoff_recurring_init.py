import pytest

from payments.services.tinkoff.tinkoff_recurring_init import TinkoffRecurringInit, TinkoffRecurringInitException


pytestmark = [
    pytest.mark.django_db,
]


def test_successful_init(factory):
    user = factory.user()
    product = factory.product()
    payment_instrument = factory.payment_instrument(user=user)
    recurrent = factory.recurrent(user=user, product=product, payment_instrument=payment_instrument, amount=1400)
    payment_id = TinkoffRecurringInit(recurrent=recurrent)()

    assert payment_id == "3093639567"


def test_init_with_custom_quantity(factory):
    user = factory.user()
    product = factory.product()
    payment_instrument = factory.payment_instrument(user=user)
    recurrent = factory.recurrent(user=user, product=product, payment_instrument=payment_instrument, amount=500)
    payment_id = TinkoffRecurringInit(recurrent=recurrent, quantity=3)()

    assert payment_id == "3093639567"


def test_init_error(monkeypatch, factory):
    user = factory.user()
    product = factory.product()
    payment_instrument = factory.payment_instrument(user=user)
    recurrent = factory.recurrent(user=user, product=product, payment_instrument=payment_instrument, amount=100)

    class ErrorResponse:
        def json(self):
            return {"Success": False, "ErrorCode": "5", "Message": "fail"}

    monkeypatch.setattr("requests.post", lambda *a, **kw: ErrorResponse())
    service = TinkoffRecurringInit(recurrent=recurrent)
    with pytest.raises(TinkoffRecurringInitException):
        service()


def test_order_id_length(factory):
    user = factory.user()
    product = factory.product()
    payment_instrument = factory.payment_instrument(user=user)
    recurrent = factory.recurrent(user=user, product=product, payment_instrument=payment_instrument)

    order_id = TinkoffRecurringInit(recurrent=recurrent).order_id

    assert isinstance(order_id, str)
    assert len(order_id) <= 50
