from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from django.db.transaction import atomic
from django.utils.timezone import now

from app.exceptions import AppServiceException
from app.services import BaseService
from payments.models import Payment, Recurrent, RecurrentChargeAttempt, RecurrentChargeStatus


class RecurrentChargeAttemptCreatorException(AppServiceException):
    """Raised when creating RecurrentChargeAttempt fails."""


@dataclass
class RecurrentChargeAttemptCreator(BaseService):
    recurrent: Recurrent
    amount: Decimal
    provider_response: dict[str, Any]
    status: str = RecurrentChargeStatus.SUCCESS
    payment: Payment | None = None
    currency: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    external_payment_id: str | None = None

    @atomic
    def act(self) -> RecurrentChargeAttempt:
        charge_attempt = RecurrentChargeAttempt(
            recurrent=self.recurrent,
            payment=self.payment or None,
            status=self.status,
            amount=self.amount,
            currency=self.currency or "rub",
            error_code=self.error_code or "",
            error_message=self.error_message or "",
            external_payment_id=self.external_payment_id or "",
            provider_response=self.provider_response,
        )
        charge_attempt.save()

        self.update_last_attempt_info(self.recurrent)

        return charge_attempt

    def update_last_attempt_info(self, recurrent: Recurrent) -> None:
        recurrent.last_attempt_charge_date = now()
        recurrent.last_attempt_charge_status = self.status

        recurrent.save(update_fields=["last_attempt_charge_date", "last_attempt_charge_status"])
