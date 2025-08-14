from datetime import datetime
from decimal import Decimal

import pytest

from payments.models import Payment, PaymentMethod, PaymentProvider, PaymentSource, PaymentStatus
from payments.services.payment_creator import PaymentCreator


pytestmark = [
    pytest.mark.django_db,
]


def test_payment_is_created(factory):
    user = factory.user()
    product = factory.product()
    payment_instrument = factory.payment_instrument(user=user)
    recurrent = factory.recurrent(user=user, product=product, payment_instrument=payment_instrument)
    payment_data = dict(
        external_payment_id="ext-123",
        order_id="order-456",
        user=user,
        product=product,
        provider=PaymentProvider.TINKOFF,
        amount=Decimal("100.00"),
        payment_instrument=payment_instrument,
        is_recurrent=True,
        recurrent=recurrent,
        source=PaymentSource.LMS,
        payment_method=PaymentMethod.CARD,
        status=PaymentStatus.PENDING,
        paid_at=datetime(2025, 8, 6, 12, 0),
        order_price=Decimal("120.00"),
        discount_price=Decimal("20.00"),
        total_price=Decimal("100.00"),
        bonus_applied=Decimal("5.00"),
        promo_code="PROMO2025",
        provider_response={"ok": True},
    )
    payment = PaymentCreator(**payment_data)()

    assert Payment.objects.count() == 1
    assert payment.external_payment_id == payment_data["external_payment_id"]
    assert payment.amount == payment_data["amount"]
    assert payment.status == PaymentStatus.PENDING
    assert payment.promo_code == "PROMO2025"
    assert payment.provider_response == {"ok": True}


def test_payment_is_updated(factory):
    user = factory.user()
    product = factory.product()
    payment_instrument = factory.payment_instrument(user=user)
    recurrent = factory.recurrent(user=user, product=product, payment_instrument=payment_instrument)
    payment_data = dict(
        external_payment_id="ext-123",
        order_id="order-456",
        user=user,
        product=product,
        provider=PaymentProvider.TINKOFF,
        amount=Decimal("100.00"),
        payment_instrument=payment_instrument,
        is_recurrent=True,
        recurrent=recurrent,
        source=PaymentSource.LMS,
        payment_method=PaymentMethod.CARD,
        status=PaymentStatus.PENDING,
        paid_at=datetime(2025, 8, 6, 12, 0),
        order_price=Decimal("120.00"),
        discount_price=Decimal("20.00"),
        total_price=Decimal("100.00"),
        bonus_applied=Decimal("5.00"),
        promo_code="PROMO2025",
        provider_response={"ok": True},
    )

    PaymentCreator(**payment_data)()

    payment_data["amount"] = Decimal("200.00")
    payment_data["status"] = PaymentStatus.PAID
    payment = PaymentCreator(**payment_data)()

    assert Payment.objects.count() == 1
    assert payment.amount == Decimal("200.00")
    assert payment.status == PaymentStatus.PAID


def test_defaults_are_applied(user, product):
    payment = PaymentCreator(
        external_payment_id="ext-456",
        order_id="order-789",
        user=user,
        product=product,
        provider=PaymentProvider.TINKOFF,
        amount=Decimal("50.00"),
    )()

    assert payment.status == PaymentStatus.PENDING
    assert payment.payment_method == PaymentMethod.CARD
    assert payment.source == PaymentSource.LMS
    assert payment.discount_price == Decimal("0.00")
    assert payment.bonus_applied == Decimal("0.00")
    assert payment.promo_code == ""
    assert payment.provider_response == {}


def test_payment_with_no_instrument_or_recurrent(user, product):
    payment = PaymentCreator(
        external_payment_id="ext-789",
        order_id="order-101",
        user=user,
        product=product,
        provider=PaymentProvider.TINKOFF,
        amount=Decimal("75.00"),
        is_recurrent=False,
    )()

    assert payment.payment_instrument is None
    assert payment.recurrent is None
    assert not payment.is_recurrent


def test_error_on_missing_required_fields(user, product):
    with pytest.raises(TypeError):
        PaymentCreator(order_id="order-111", user=user, product=product, provider=PaymentProvider.TINKOFF, amount=Decimal("10.00"))()


def test_paid_at_is_set(user, product):
    payment = PaymentCreator(
        external_payment_id="ext-999",
        order_id="order-999",
        user=user,
        product=product,
        provider=PaymentProvider.TINKOFF,
        amount=Decimal("99.00"),
    )()

    assert payment.paid_at is not None
    assert isinstance(payment.paid_at, datetime)


def test_total_price_and_order_price_defaults(user, product):
    payment = PaymentCreator(
        external_payment_id="ext-555",
        order_id="order-555",
        user=user,
        product=product,
        provider=PaymentProvider.TINKOFF,
        amount=Decimal("55.00"),
    )()

    assert payment.total_price == Decimal("55.00")
    assert payment.order_price == Decimal("55.00")
