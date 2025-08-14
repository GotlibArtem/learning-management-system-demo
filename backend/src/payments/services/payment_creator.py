from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from django.db.transaction import atomic
from django.utils.timezone import now

from app.exceptions import AppServiceException
from app.services import BaseService
from payments.models import (
    Payment,
    PaymentInstrument,
    PaymentMethod,
    PaymentProvider,
    PaymentSource,
    PaymentStatus,
    Recurrent,
)
from products.models import Product
from users.models import User


class PaymentCreatorException(AppServiceException):
    """Raised when creating Payment for recurrent charge fails."""


@dataclass
class PaymentCreator(BaseService):
    external_payment_id: str
    order_id: str
    user: User
    product: Product
    provider: PaymentProvider
    amount: Decimal
    payment_instrument: PaymentInstrument | None = None
    is_recurrent: bool = False
    recurrent: Recurrent | None = None
    source: str | None = PaymentSource.LMS
    payment_method: str | None = PaymentMethod.CARD
    status: str | None = PaymentStatus.PENDING
    paid_at: datetime | None = None
    order_price: Decimal | None = None
    discount_price: Decimal = Decimal("0.00")
    total_price: Decimal | None = None
    bonus_applied: Decimal = Decimal("0.00")
    promo_code: str = ""
    provider_response: dict[str, Any] | None = None

    @atomic
    def act(self) -> Payment:
        payment, _ = Payment.objects.update_or_create(
            external_payment_id=self.external_payment_id,
            defaults=dict(
                order_id=self.order_id,
                user=self.user,
                product=self.product,
                provider=self.provider,
                amount=self.amount,
                payment_instrument=self.payment_instrument or None,
                is_recurrent=self.is_recurrent or False,
                recurrent=self.recurrent or None,
                source=self.source or PaymentSource.LMS,
                payment_method=self.payment_method or PaymentMethod.CARD,
                status=self.status or PaymentStatus.PENDING,
                paid_at=self.paid_at or now(),
                order_price=self.order_price or self.amount,
                discount_price=self.discount_price or Decimal("0.00"),
                total_price=self.total_price or self.amount,
                bonus_applied=self.bonus_applied or Decimal("0.00"),
                promo_code=self.promo_code,
                provider_response=self.provider_response or {},
            ),
        )

        return payment
