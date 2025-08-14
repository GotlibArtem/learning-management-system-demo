import pytest
from django.utils.timezone import now

from payments.models import PaymentInstrumentStatus, RecurrentStatus
from users.services import UserRecurrentInfoGetter, UserRecurrentInfoGetterException


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
        amount="999.00",
        next_charge_date=now(),
    )


def test_returns_payload_for_active_recurrent_and_active_instrument(user, recurrent):
    payload = UserRecurrentInfoGetter(user=user)()

    assert payload["product_name"] == recurrent.product.name
    assert str(payload["amount"]) == str(recurrent.amount)
    assert payload["next_charge_date"] == recurrent.next_charge_date
    assert payload["card_mask"].startswith("**** **** **** ")
    assert len(payload["card_mask"].split()[-1]) == 4


@pytest.mark.parametrize(
    ("raw_mask", "expected_suffix"),
    [
        ("2200 70** **** 4198", "4198"),
        ("**** **** **** 4198", "4198"),
        ("  1234  ", "1234"),
        ("****1234", "1234"),
        ("abcd", None),
    ],
)
def test_card_mask_is_normalized(user, product, payment_instrument, factory, raw_mask, expected_suffix):
    payment_instrument.card_mask = raw_mask
    payment_instrument.save(update_fields=["card_mask"])
    factory.recurrent(
        user=user,
        product=product,
        payment_instrument=payment_instrument,
        status=RecurrentStatus.ACTIVE,
        amount="100.00",
        next_charge_date=now(),
    )

    payload = UserRecurrentInfoGetter(user=user)()

    if expected_suffix:
        assert payload["card_mask"] == f"**** **** **** {expected_suffix}"
    else:
        assert payload["card_mask"] == "**** **** **** ****"


def test_next_charge_date_can_be_none(user, product, payment_instrument, factory):
    factory.recurrent(
        user=user,
        product=product,
        payment_instrument=payment_instrument,
        status=RecurrentStatus.ACTIVE,
        amount="10.00",
        next_charge_date=None,
    )

    payload = UserRecurrentInfoGetter(user=user)()
    assert payload["next_charge_date"] is None


def test_raises_if_no_active_recurrent(user):
    with pytest.raises(UserRecurrentInfoGetterException, match="active recurrent"):
        UserRecurrentInfoGetter(user=user)()


def test_raises_if_recurrent_is_inactive(user, product, payment_instrument, factory):
    factory.recurrent(
        user=user,
        product=product,
        payment_instrument=payment_instrument,
        status=RecurrentStatus.CANCELLED,
    )

    with pytest.raises(UserRecurrentInfoGetterException, match="active recurrent"):
        UserRecurrentInfoGetter(user=user)()


def test_raises_if_no_payment_instrument(user, product, factory):
    factory.recurrent(
        user=user,
        product=product,
        payment_instrument=None,
        status=RecurrentStatus.ACTIVE,
    )

    with pytest.raises(UserRecurrentInfoGetterException, match="active payment instrument"):
        UserRecurrentInfoGetter(user=user)()


def test_raises_if_payment_instrument_is_not_active(user, product, payment_instrument, factory):
    payment_instrument.status = PaymentInstrumentStatus.INACTIVE
    payment_instrument.save(update_fields=["status"])

    factory.recurrent(
        user=user,
        product=product,
        payment_instrument=payment_instrument,
        status=RecurrentStatus.ACTIVE,
    )

    with pytest.raises(UserRecurrentInfoGetterException, match="active payment instrument"):
        UserRecurrentInfoGetter(user=user)()
