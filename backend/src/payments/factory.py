from typing import Any

from app.testing import register
from app.testing.types import FactoryProtocol
from payments.models import Payment, PaymentInstrument, Recurrent, RecurrentChargeAttempt


@register
def payment_instrument(self: FactoryProtocol, **kwargs: Any) -> PaymentInstrument:
    defaults = {
        "user": kwargs.get("user"),
        "provider": kwargs.get("provider", "TINKOFF"),
        "payment_method": kwargs.get("payment_method", "CARD"),
        "rebill_id": kwargs.get("rebill_id", "rebill-123"),
        "card_mask": kwargs.get("card_mask", "220220******7382"),
        "exp_date": kwargs.get("exp_date", "0925"),
        "card_id": kwargs.get("card_id", "card-456"),
        "status": kwargs.get("status", "ACTIVE"),
        "token": kwargs.get("token", "tok-abc123"),
    }
    return PaymentInstrument.objects.create(**defaults)


@register
def payment(self: FactoryProtocol, **kwargs: Any) -> Payment:
    defaults = {
        "external_payment_id": kwargs.get("external_payment_id", "ext-123"),
        "order_id": kwargs.get("order_id", "order-456"),
        "user": kwargs.get("user"),
        "product": kwargs.get("product"),
        "payment_instrument": kwargs.get("payment_instrument"),
        "source": kwargs.get("source", "SITE"),
        "provider": kwargs.get("provider", "TINKOFF"),
        "payment_method": kwargs.get("payment_method", "CARD"),
        "status": kwargs.get("status", "PAID"),
        "paid_at": kwargs.get("paid_at"),
        "order_price": kwargs.get("order_price", 100),
        "total_price": kwargs.get("total_price", 90),
        "discount_price": kwargs.get("discount_price", 10),
        "amount": kwargs.get("amount", 90),
        "bonus_applied": kwargs.get("bonus_applied", 0),
        "promo_code": kwargs.get("promo_code", ""),
        "is_recurrent": kwargs.get("is_recurrent", False),
        "provider_response": kwargs.get("provider_response", {}),
    }
    return Payment.objects.create(**defaults)


@register
def recurrent(self: FactoryProtocol, **kwargs: Any) -> Recurrent:
    defaults = {
        "user": kwargs.get("user"),
        "product": kwargs.get("product"),
        "payment_instrument": kwargs.get("payment_instrument"),
        "status": kwargs.get("status", "ACTIVE"),
        "amount": kwargs.get("amount", 90),
        "next_charge_date": kwargs.get("next_charge_date"),
        "last_attempt_charge_date": kwargs.get("last_attempt_charge_date"),
        "last_attempt_charge_status": kwargs.get("last_attempt_charge_status", ""),
    }
    return Recurrent.objects.create(**defaults)


@register
def recurrent_charge_attempt(self: FactoryProtocol, **kwargs: Any) -> RecurrentChargeAttempt:
    defaults = {
        "recurrent": kwargs.get("recurrent"),
        "payment": kwargs.get("payment"),
        "status": kwargs.get("status", "SUCCESS"),
        "amount": kwargs.get("amount", 90),
        "currency": kwargs.get("currency", "RUB"),
        "external_payment_id": kwargs.get("external_payment_id", "ext-123"),
    }
    return RecurrentChargeAttempt.objects.create(**defaults)
