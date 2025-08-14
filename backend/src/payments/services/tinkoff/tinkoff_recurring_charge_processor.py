import traceback
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

import sentry_sdk
from django.db.transaction import on_commit
from django.utils.functional import cached_property
from django.utils.timezone import now

from app.exceptions import AppServiceException
from app.services import BaseService
from mindbox.tasks import send_payment_attempt
from payments.models import (
    ChargeAttemptLog,
    Payment,
    PaymentMethod,
    PaymentProvider,
    PaymentSource,
    PaymentStatus,
    Recurrent,
    RecurrentChargeAttempt,
    RecurrentChargeStatus,
)
from payments.services.tinkoff import TinkoffRecurringCharge, TinkoffRecurringInit


class TinkoffRecurringChargeProcessorException(AppServiceException):
    """Raised when Tinkoff recurring charge processing fails."""


@dataclass
class TinkoffRecurringChargeProcessor(BaseService):
    recurrent: Recurrent

    def act(self) -> tuple[Payment | None, RecurrentChargeAttempt | None]:
        recurring_charge: dict[str, Any] | None = None

        try:
            payment_id = TinkoffRecurringInit(self.recurrent)()
            recurring_charge = TinkoffRecurringCharge(self.recurrent, payment_id)()

            if not recurring_charge:
                return None, None

            payment = self.create_payment(recurring_charge, payment_id)
            last_charge_attempt = self.create_charge_attempt(recurring_charge, payment)

            return payment, last_charge_attempt

        except TinkoffRecurringChargeProcessorException as exc:
            self._log_error(exc, recurring_charge)
            raise

    def create_payment(self, recurring_charge: dict[str, Any], payment_id: str) -> Payment | None:
        from payments.services import PaymentCreator

        if self.get_charge_status(recurring_charge) != RecurrentChargeStatus.SUCCESS:
            return None

        return PaymentCreator(
            external_payment_id=recurring_charge.get("PaymentId", payment_id),
            order_id=recurring_charge.get("OrderId") or f"{self.recurrent.id.hex}-{int(now().timestamp())}",
            user=self.recurrent.user,
            product=self.recurrent.product,
            provider=PaymentProvider.TINKOFF,
            amount=self.get_amount(recurring_charge),
            payment_instrument=self.recurrent.payment_instrument or None,
            is_recurrent=True,
            recurrent=self.recurrent,
            source=PaymentSource.LMS,
            payment_method=self.payment_method,
            status=PaymentStatus.PAID,
            paid_at=now(),
            provider_response=recurring_charge,
        )()

    def create_charge_attempt(self, recurring_charge: dict[str, Any], payment: Payment | None) -> RecurrentChargeAttempt:
        from payments.services import RecurrentChargeAttemptCreator

        recurring_charge_attempt = RecurrentChargeAttemptCreator(
            recurrent=self.recurrent,
            amount=self.get_amount(recurring_charge),
            provider_response=recurring_charge,
            status=self.get_charge_status(recurring_charge),
            payment=payment,
            currency="rub",
            error_code=recurring_charge.get("ErrorCode", ""),
            error_message=recurring_charge.get("Details") or recurring_charge.get("Message") or "",
            external_payment_id=recurring_charge.get("PaymentId", ""),
        )()

        on_commit(lambda: send_payment_attempt.delay(str(self.recurrent.user.id), str(recurring_charge_attempt.id)))

        return recurring_charge_attempt

    @cached_property
    def payment_method(self) -> str:
        return self.recurrent.payment_instrument.payment_method if self.recurrent.payment_instrument else PaymentMethod.CARD_RECURRENT

    def get_amount(self, recurring_charge: dict[str, Any]) -> Decimal:
        return Decimal(recurring_charge.get("Amount") or 0) / 100

    def get_charge_status(self, recurring_charge: dict[str, Any]) -> str:
        return (
            RecurrentChargeStatus.SUCCESS if recurring_charge.get("Success") and recurring_charge.get("Status") == "CONFIRMED" else RecurrentChargeStatus.FAIL
        )

    def _log_error(self, exc: Exception, response: dict[str, Any] | None = None) -> None:
        try:
            ChargeAttemptLog.objects.create(
                user=self.recurrent.user,
                external_payment_id=str(response.get("PaymentId")) if response else "",
                provider=self.recurrent.payment_instrument.provider if self.recurrent.payment_instrument else "",
                provider_response=response or {},
                error_message=str(exc),
                traceback=traceback.format_exc(),
            )
        except Exception as e:  # noqa: BLE001
            sentry_sdk.capture_exception(e)
