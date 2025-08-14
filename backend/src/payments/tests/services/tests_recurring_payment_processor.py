from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils.timezone import now

from payments.models import Payment, PaymentProvider, PaymentStatus, RecurrentChargeAttempt, RecurrentChargeStatus
from payments.services.recurring_payment_processor import MAX_CHARGE_ATTEMPTS, RecurringPaymentProcessor, RecurringPaymentProcessorException
from product_access.models import ProductAccess


pytestmark = [
    pytest.mark.django_db,
]


def make_recurrent(
    factory,
    status="ACTIVE",
    amount=1000,
    payment_instrument_kwargs=None,
    next_charge_date=None,
    last_attempt_charge_status="",
    last_attempt_charge_date=None,
):
    user = factory.user()
    product = factory.product(lifetime=365)
    payment_instrument = factory.payment_instrument(user=user, **(payment_instrument_kwargs or {}))
    return factory.recurrent(
        user=user,
        product=product,
        payment_instrument=payment_instrument,
        status=status,
        amount=amount,
        next_charge_date=next_charge_date or now(),
        last_attempt_charge_status=last_attempt_charge_status,
        last_attempt_charge_date=last_attempt_charge_date,
    )


def test_successful_payment_grants_access(factory, monkeypatch):
    recurrent = make_recurrent(factory, last_attempt_charge_status=RecurrentChargeStatus.FAIL)
    payment = type("Payment", (), {"status": PaymentStatus.PAID, "amount": 1000, "order_id": "order-123"})()
    monkeypatch.setattr("payments.services.TinkoffRecurringChargeProcessor.act", lambda self: (payment, None))
    RecurringPaymentProcessor(recurrent=recurrent)()

    access = ProductAccess.objects.filter(user=recurrent.user, product=recurrent.product, order_id="order-123").first()

    assert access is not None


def test_deactivate_on_max_attempts(factory, monkeypatch):
    recurrent = make_recurrent(factory)

    def charge_processor_act(self):
        RecurrentChargeAttempt.objects.create(recurrent=recurrent, status=RecurrentChargeStatus.FAIL, amount=1000)
        return (None, None)

    monkeypatch.setattr("payments.services.TinkoffRecurringChargeProcessor.act", charge_processor_act)

    for _ in range(MAX_CHARGE_ATTEMPTS - 1):
        RecurrentChargeAttempt.objects.create(recurrent=recurrent, status=RecurrentChargeStatus.FAIL, amount=1000)

    RecurringPaymentProcessor(recurrent=recurrent)()
    recurrent.refresh_from_db()

    assert recurrent.is_active() is False


def test_validate_recurrent_status_inactive(factory):
    recurrent = make_recurrent(factory, status="INACTIVE")
    processor = RecurringPaymentProcessor(recurrent=recurrent)

    with pytest.raises(RecurringPaymentProcessorException, match="Recurrent is not active"):
        processor.validate_recurrent_status()


def test_validate_payment_instrument_missing(factory):
    recurrent = make_recurrent(factory)
    recurrent.payment_instrument = None
    processor = RecurringPaymentProcessor(recurrent=recurrent)

    with pytest.raises(RecurringPaymentProcessorException, match="Missing payment instrument"):
        processor.validate_payment_instrument()


def test_validate_payment_instrument_is_not_active(factory):
    recurrent = make_recurrent(factory)
    recurrent.payment_instrument.status = "INACTIVE"
    processor = RecurringPaymentProcessor(recurrent=recurrent)

    with pytest.raises(RecurringPaymentProcessorException, match="Payment instrument is not active"):
        processor.validate_payment_instrument()


def test_validate_next_charge_date_in_future(factory):
    from datetime import timedelta

    recurrent = make_recurrent(factory, next_charge_date=now() + timedelta(days=1))
    processor = RecurringPaymentProcessor(recurrent=recurrent)

    with pytest.raises(RecurringPaymentProcessorException, match="Next charge date is in the future"):
        processor.validate_next_charge_date()


def test_validate_last_successful_charge_not_before_next(factory):
    dt = now()
    recurrent = make_recurrent(
        factory,
        last_attempt_charge_status=RecurrentChargeStatus.SUCCESS,
        next_charge_date=dt,
        last_attempt_charge_date=dt + timedelta(days=1),
    )
    processor = RecurringPaymentProcessor(recurrent=recurrent)

    with pytest.raises(RecurringPaymentProcessorException, match="Last successful charge is not before next charge date"):
        processor.validate_last_successful_charge()


def test_validate_charge_attempts_count_exceeded(factory):
    recurrent = make_recurrent(factory)
    for _ in range(MAX_CHARGE_ATTEMPTS):
        RecurrentChargeAttempt.objects.create(recurrent=recurrent, created=now(), status=RecurrentChargeStatus.FAIL, amount=1000)
    processor = RecurringPaymentProcessor(recurrent=recurrent)

    with pytest.raises(RecurringPaymentProcessorException, match="Too many charge attempts"):
        processor.validate_charge_attempts_count()


def test_validate_payment_exists_for_today(factory):
    recurrent = make_recurrent(factory)
    Payment.objects.create(
        external_payment_id="ext-001",
        order_id="order-001",
        user=recurrent.user,
        product=recurrent.product,
        provider=PaymentProvider.TINKOFF,
        order_price=Decimal("1000.00"),
        total_price=Decimal("1000.00"),
        amount=Decimal("1000.00"),
        status=PaymentStatus.PAID,
        paid_at=now(),
        is_recurrent=True,
        recurrent=recurrent,
    )
    processor = RecurringPaymentProcessor(recurrent=recurrent)

    with pytest.raises(RecurringPaymentProcessorException, match="Payment for today already exists"):
        processor.validate_payment_exists()


def test_unsupported_provider(factory):
    recurrent = make_recurrent(factory)
    recurrent.payment_instrument.provider = "SBER"
    processor = RecurringPaymentProcessor(recurrent=recurrent)

    with pytest.raises(RecurringPaymentProcessorException, match="Unsupported payment provider"):
        processor.run_charge()


def test_error_logging(factory, monkeypatch):
    recurrent = make_recurrent(factory)
    monkeypatch.setattr("payments.services.TinkoffRecurringChargeProcessor.act", lambda self: (_ for _ in ()).throw(RecurringPaymentProcessorException("fail")))
    processor = RecurringPaymentProcessor(recurrent=recurrent)

    with pytest.raises(RecurringPaymentProcessorException, match="fail"):
        processor()
