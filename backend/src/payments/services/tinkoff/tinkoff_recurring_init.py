import traceback
from dataclasses import dataclass
from typing import Any

import requests
import sentry_sdk
from django.conf import settings
from django.utils.functional import cached_property
from django.utils.timezone import now

from app.exceptions import AppServiceException
from app.services import BaseService
from payments.models import ChargeAttemptLog, Recurrent
from payments.services.tinkoff.tinkoff_token_generator import TinkoffTokenGenerator
from products.models import Product


class TinkoffRecurringInitException(AppServiceException):
    """Raised when Init request to Tinkoff fails."""


@dataclass
class TinkoffRecurringInit(BaseService):
    """Initializes payment in Tinkoff for future recurrent charge (without redirection)."""

    recurrent: Recurrent
    quantity: int = 1

    def act(self) -> str:
        try:
            payload = self.payload
            token = TinkoffTokenGenerator(payload)()
            full_payload = {
                **payload,
                "Token": token,
            }

            return self.post_tinkoff_init(full_payload)

        except Exception as exc:
            self._log_error(exc)
            raise

    def post_tinkoff_init(self, payload: dict[str, Any]) -> str:
        url = f"{settings.TINKOFF_API_URL}/Init"
        response = requests.post(url, json=payload, timeout=20)
        data = response.json()

        if not data.get("Success") or not data.get("PaymentId"):
            raise TinkoffRecurringInitException(f"Tinkoff Init failed: {data}")

        return str(data["PaymentId"])

    @cached_property
    def product(self) -> Product:
        return self.recurrent.product

    @cached_property
    def amount(self) -> int:
        return int(self.recurrent.amount * 100)  # in kopecks

    @cached_property
    def total_amount(self) -> int:
        return self.amount * self.quantity

    @cached_property
    def order_id(self) -> str:
        return f"{self.recurrent.id.hex}-{int(now().timestamp())}"

    @cached_property
    def payload(self) -> dict[str, Any]:
        return {
            "TerminalKey": settings.TINKOFF_TERMINAL_KEY,
            "Amount": self.amount,
            "OrderId": self.order_id,
            "Description": self.product.name,
            "Receipt": self.receipt,
        }

    @cached_property
    def receipt(self) -> dict[str, Any]:
        return {
            "Email": self.recurrent.user.username,
            "Phone": self.recurrent.user.phone or "",
            "Taxation": settings.TINKOFF_TAXATION,
            "Items": [
                {
                    "Name": self.product.name,
                    "Price": self.amount,
                    "Quantity": self.quantity,
                    "Amount": self.total_amount,
                    "Tax": settings.TINKOFF_TAX,
                    "PaymentObject": settings.TINKOFF_PAYMENT_OBJECT,
                },
            ],
        }

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
