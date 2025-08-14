import traceback
from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta

import sentry_sdk
from django.utils.timezone import now
from django.utils.translation import gettext as _

from app.exceptions import AppServiceException
from app.services import BaseService
from payments.models import (
    ChargeAttemptLog,
    Payment,
    PaymentInstrumentStatus,
    PaymentProvider,
    PaymentStatus,
    Recurrent,
    RecurrentChargeAttempt,
    RecurrentChargeStatus,
)


MAX_CHARGE_ATTEMPTS = 3


class RecurringPaymentProcessorException(AppServiceException):
    """Raised when recurring payment processor fails."""


@dataclass
class RecurringPaymentProcessor(BaseService):
    recurrent: Recurrent

    def act(self) -> None:
        try:
            payment, _ = self.run_charge()
            self.recurrent.refresh_from_db()

            if not payment:
                self.maybe_deactivate_recurrent()
                return

            self.update_next_charge_date()
            self.grant_access_to_product(payment)

        except RecurringPaymentProcessorException as exc:
            self._log_error(exc)
            raise

    def run_charge(self) -> tuple[Payment | None, RecurrentChargeAttempt | None]:
        from payments.services import TinkoffRecurringChargeProcessor

        assert self.recurrent.payment_instrument is not None

        if self.recurrent.payment_instrument.provider == PaymentProvider.TINKOFF:
            return TinkoffRecurringChargeProcessor(self.recurrent)()

        raise RecurringPaymentProcessorException(_("Unsupported payment provider."))

    def maybe_deactivate_recurrent(self) -> None:
        attempts_count = RecurrentChargeAttempt.objects.filter(
            recurrent=self.recurrent,
            created__gte=self.recurrent.next_charge_date,
        ).count()

        if attempts_count >= MAX_CHARGE_ATTEMPTS:
            self.recurrent.deactivate()

    def update_next_charge_date(self) -> None:
        self.recurrent.update_next_charge_date()

    def grant_access_to_product(self, payment: Payment) -> None:
        from product_access.services import ProductAccessProvider

        start_date = self.recurrent.last_attempt_charge_date.date() if self.recurrent.last_attempt_charge_date else now().date()
        end_date = (
            self.recurrent.next_charge_date.date() if self.recurrent.next_charge_date else (now().date() + timedelta(days=self.recurrent.product.lifetime))  # type: ignore[arg-type]
        )

        ProductAccessProvider(
            user=self.recurrent.user,
            product=self.recurrent.product,
            start_date=start_date,
            end_date=end_date,
            order_id=payment.order_id,
            access_granted_time=now(),
        )()

    def get_validators(self) -> list[Callable]:
        return [
            self.validate_recurrent_status,
            self.validate_payment_instrument,
            self.validate_next_charge_date,
            self.validate_last_successful_charge,
            self.validate_charge_attempts_count,
            self.validate_payment_exists,
        ]

    def validate_recurrent_status(self) -> None:
        if not self.recurrent.is_active():
            raise RecurringPaymentProcessorException(_("Recurrent is not active."))

    def validate_payment_instrument(self) -> None:
        payment_instrument = self.recurrent.payment_instrument
        if not payment_instrument:
            raise RecurringPaymentProcessorException(_("Missing payment instrument."))

        if payment_instrument.status != PaymentInstrumentStatus.ACTIVE:
            raise RecurringPaymentProcessorException(_("Payment instrument is not active."))

    def validate_next_charge_date(self) -> None:
        if not self.recurrent.next_charge_date or self.recurrent.next_charge_date > now():
            raise RecurringPaymentProcessorException(_("Next charge date is in the future."))

    def validate_last_successful_charge(self) -> None:
        if (
            self.recurrent.last_attempt_charge_status == RecurrentChargeStatus.SUCCESS
            and self.recurrent.last_attempt_charge_date
            and self.recurrent.next_charge_date
            and self.recurrent.last_attempt_charge_date >= self.recurrent.next_charge_date
        ):
            raise RecurringPaymentProcessorException(_("Last successful charge is not before next charge date."))

    def validate_charge_attempts_count(self) -> None:
        attempts_count = RecurrentChargeAttempt.objects.filter(
            recurrent=self.recurrent,
            created__gte=self.recurrent.next_charge_date,
        ).count()

        if attempts_count >= MAX_CHARGE_ATTEMPTS:
            raise RecurringPaymentProcessorException(_("Too many charge attempts."))

    def validate_payment_exists(self) -> None:
        if Payment.objects.filter(
            user=self.recurrent.user,
            product=self.recurrent.product,
            status=PaymentStatus.PAID,
            paid_at__gte=self.recurrent.next_charge_date,
        ).exists():
            raise RecurringPaymentProcessorException(_("Payment for today already exists."))

    def _log_error(self, exc: Exception) -> None:
        try:
            ChargeAttemptLog.objects.create(
                user=self.recurrent.user,
                provider=self.recurrent.payment_instrument.provider if self.recurrent.payment_instrument else "",
                error_message=str(exc),
                traceback=traceback.format_exc(),
            )
        except Exception as e:  # noqa: BLE001
            sentry_sdk.capture_exception(e)
