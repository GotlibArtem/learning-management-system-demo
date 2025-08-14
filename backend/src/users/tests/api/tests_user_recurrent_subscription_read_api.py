import pytest
from django.utils.timezone import now
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
        amount="999.00",
        next_charge_date=now(),
    )


def test_get_recurrent_subscription_ok(as_user, recurrent_active):
    got = as_user.get(base_url, expected_status=status.HTTP_200_OK)

    assert got["productName"] == recurrent_active.product.name
    assert str(got["amount"]) == str(recurrent_active.amount)
    assert got["nextChargeDate"]
    assert got["cardMask"].startswith("**** **** **** ")
    assert len(got["cardMask"].split()[-1]) == 4


@pytest.mark.parametrize(
    ("raw_mask", "expected"),
    [
        ("2200 70** **** 4198", "**** **** **** 4198"),
        ("**** **** **** 4198", "**** **** **** 4198"),
    ],
)
def test_card_mask_is_normalized(as_user, recurrent_active, payment_instrument, raw_mask, expected):
    payment_instrument.setattr_and_save("card_mask", raw_mask)

    got = as_user.get(base_url, expected_status=status.HTTP_200_OK)

    assert got["cardMask"] == expected


def test_next_charge_date_can_be_none(as_user, recurrent_active):
    recurrent_active.setattr_and_save("next_charge_date", None)

    got = as_user.get(base_url, expected_status=status.HTTP_200_OK)

    assert got["nextChargeDate"] is None


def test_400_if_no_active_recurrent(as_user):
    as_user.get(base_url, expected_status=status.HTTP_400_BAD_REQUEST)


def test_400_if_recurrent_is_inactive(as_user, recurrent_active):
    recurrent_active.setattr_and_save("status", RecurrentStatus.CANCELLED)

    as_user.get(base_url, expected_status=status.HTTP_400_BAD_REQUEST)


def test_400_if_no_payment_instrument(as_user, recurrent_active):
    recurrent_active.setattr_and_save("payment_instrument", None)

    as_user.get(base_url, expected_status=status.HTTP_400_BAD_REQUEST)


def test_400_if_payment_instrument_is_inactive(as_user, recurrent_active, payment_instrument):
    payment_instrument.setattr_and_save("status", PaymentInstrumentStatus.INACTIVE)

    as_user.get(base_url, expected_status=status.HTTP_400_BAD_REQUEST)


def test_anon_forbidden(as_anon):
    as_anon.get(base_url, expected_status=status.HTTP_401_UNAUTHORIZED)
