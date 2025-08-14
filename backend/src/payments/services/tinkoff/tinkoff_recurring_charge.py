import traceback
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import requests
import sentry_sdk
from django.conf import settings
from django.utils.functional import cached_property

from app.exceptions import AppServiceException
from app.services import BaseService
from payments.models import ChargeAttemptLog, Recurrent
from payments.services.tinkoff.tinkoff_token_generator import TinkoffTokenGenerator


class TinkoffRecurringChargeException(AppServiceException):
    """Raised when Charge request to Tinkoff fails."""


@dataclass
class TinkoffRecurringCharge(BaseService):
    """Performs recurrent charge in Tinkoff by RebillId and PaymentId."""

    recurrent: Recurrent
    payment_id: str

    def act(self) -> dict[str, Any]:
        try:
            payload = self.payload
            token = TinkoffTokenGenerator(payload)()
            full_payload = {
                **payload,
                "Token": token,
            }

            return self.post_tinkoff_charge(full_payload)

        except Exception as exc:
            self._log_error(exc)
            raise

    def post_tinkoff_charge(self, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{settings.TINKOFF_API_URL}/Charge"
        response = requests.post(url, json=payload, timeout=20)
        response.json()
        return response.json()

    @cached_property
    def payload(self) -> dict[str, Any]:
        return {
            "TerminalKey": settings.TINKOFF_TERMINAL_KEY,
            "PaymentId": self.payment_id,
            "RebillId": self.rebill_id,
            "SendEmail": True,
            "InfoEmail": self.recurrent.user.username,
        }

    @cached_property
    def rebill_id(self) -> str:
        instrument = self.recurrent.payment_instrument
        if not instrument or not instrument.rebill_id:
            raise TinkoffRecurringChargeException("Missing RebillId for recurrent.")
        return instrument.rebill_id

    def get_validators(self) -> list[Callable]:
        return [
            self.validate_recurrent_status,
        ]

    def validate_recurrent_status(self) -> None:
        if not self.recurrent.is_active():
            raise TinkoffRecurringChargeException("Recurrent is not active.")

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
