import pytest

from payments.models import PaymentInstrumentStatus, Recurrent, RecurrentStatus
from users.services import UserRecurrentCanceller, UserRecurrentCancellerException


pytestmark = [
    pytest.mark.django_db,
]


@pytest.fixture
def subscription_product(product):
    product.setattr_and_save("product_type", "subscription")
    return product


@pytest.fixture
def recurrent(factory, user, subscription_product, payment_instrument):
    return factory.recurrent(
        user=user,
        product=subscription_product,
        payment_instrument=payment_instrument,
        status=RecurrentStatus.ACTIVE,
        amount="199.00",
    )


def test_cancels_recurrent_and_deactivates_instrument(user, recurrent):
    instrument = recurrent.payment_instrument

    UserRecurrentCanceller(user=user)()

    recurrent.refresh_from_db()
    instrument.refresh_from_db()
    assert recurrent.status == RecurrentStatus.CANCELLED
    assert instrument.status == PaymentInstrumentStatus.INACTIVE


def test_raises_if_no_recurrent(user):
    with pytest.raises(UserRecurrentCancellerException, match="recurrent subscription"):
        UserRecurrentCanceller(user=user)()


def test_raises_if_payment_instrument_missing(user, recurrent):
    recurrent.setattr_and_save("payment_instrument", None)

    with pytest.raises(UserRecurrentCancellerException, match="payment instrument"):
        UserRecurrentCanceller(user=user)()


def test_succeeds_if_payment_instrument_inactive(user, recurrent):
    instrument = recurrent.payment_instrument
    instrument.setattr_and_save("status", PaymentInstrumentStatus.INACTIVE)

    UserRecurrentCanceller(user=user)()

    recurrent.refresh_from_db()
    instrument.refresh_from_db()
    assert recurrent.status == RecurrentStatus.CANCELLED
    assert instrument.status == PaymentInstrumentStatus.INACTIVE


def test_succeeds_if_recurrent_already_cancelled(user, recurrent):
    UserRecurrentCanceller(user=user)()
    UserRecurrentCanceller(user=user)()

    recurrent.refresh_from_db()
    assert recurrent.status == RecurrentStatus.CANCELLED
    assert recurrent.payment_instrument.status == PaymentInstrumentStatus.INACTIVE


def test_not_affect_other_users(factory, recurrent):
    other = factory.user()

    with pytest.raises(UserRecurrentCancellerException, match="recurrent subscription"):
        UserRecurrentCanceller(user=other)()

    recurrent.refresh_from_db()
    assert recurrent.status == RecurrentStatus.ACTIVE


def test_cancels_recurrent_even_if_instrument_already_inactive(user, recurrent):
    recurrent.payment_instrument.setattr_and_save("status", PaymentInstrumentStatus.INACTIVE)

    UserRecurrentCanceller(user=user)()

    recurrent.refresh_from_db()
    assert recurrent.status == RecurrentStatus.CANCELLED


def test_atomic_rollback_on_failure(user, recurrent, mocker):
    instrument = recurrent.payment_instrument

    mocker.patch.object(Recurrent, "save", side_effect=Exception("boom"))

    with pytest.raises(Exception, match="boom"):
        UserRecurrentCanceller(user=user)()

    recurrent.refresh_from_db()
    instrument.refresh_from_db()

    assert recurrent.status == RecurrentStatus.ACTIVE
    assert instrument.status == PaymentInstrumentStatus.ACTIVE
