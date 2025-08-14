import pytest
from rest_framework import status

from payments.models import PaymentInstrumentStatus, RecurrentStatus


pytestmark = [
    pytest.mark.django_db,
]


base_url = "/api/demo/users/recurrent-subscription/"


@pytest.fixture
def subscription_product(product):
    product.setattr_and_save("product_type", "subscription")
    return product


@pytest.fixture
def recurrent_active(factory, user, subscription_product, payment_instrument):
    return factory.recurrent(
        user=user,
        product=subscription_product,
        payment_instrument=payment_instrument,
        status=RecurrentStatus.ACTIVE,
        amount="199.00",
    )


def test_delete_cancels_recurrent_and_deactivates_instrument(as_user, recurrent_active):
    instrument = recurrent_active.payment_instrument

    as_user.delete(base_url, expected_status=status.HTTP_204_NO_CONTENT)

    recurrent_active.refresh_from_db()
    instrument.refresh_from_db()
    assert recurrent_active.status == RecurrentStatus.CANCELLED
    assert instrument.status == PaymentInstrumentStatus.INACTIVE


def test_delete_is_idempotent(as_user, recurrent_active):
    as_user.delete(base_url, expected_status=status.HTTP_204_NO_CONTENT)
    as_user.delete(base_url, expected_status=status.HTTP_204_NO_CONTENT)

    recurrent_active.refresh_from_db()
    assert recurrent_active.status == RecurrentStatus.CANCELLED
    assert recurrent_active.payment_instrument.status == PaymentInstrumentStatus.INACTIVE


def test_delete_succeeds_if_instrument_already_inactive(as_user, recurrent_active, payment_instrument):
    payment_instrument.setattr_and_save("status", PaymentInstrumentStatus.INACTIVE)

    as_user.delete(base_url, expected_status=status.HTTP_204_NO_CONTENT)

    recurrent_active.refresh_from_db()
    assert recurrent_active.status == RecurrentStatus.CANCELLED
    assert recurrent_active.payment_instrument.status == PaymentInstrumentStatus.INACTIVE


def test_delete_succeeds_if_recurrent_already_cancelled(as_user, recurrent_active):
    recurrent_active.setattr_and_save("status", RecurrentStatus.CANCELLED)

    as_user.delete(base_url, expected_status=status.HTTP_204_NO_CONTENT)

    recurrent_active.refresh_from_db()
    assert recurrent_active.status == RecurrentStatus.CANCELLED
    assert recurrent_active.payment_instrument.status == PaymentInstrumentStatus.INACTIVE


def test_delete_400_if_no_recurrent(as_user):
    as_user.delete(base_url, expected_status=status.HTTP_400_BAD_REQUEST)


def test_delete_400_if_no_payment_instrument(as_user, recurrent_active):
    recurrent_active.setattr_and_save("payment_instrument", None)

    as_user.delete(base_url, expected_status=status.HTTP_400_BAD_REQUEST)


def test_delete_anon_forbidden(as_anon):
    as_anon.delete(base_url, expected_status=status.HTTP_401_UNAUTHORIZED)
