from dataclasses import dataclass

from django.utils.translation import gettext_lazy as _

from app.exceptions import AppServiceException
from app.services import BaseService
from payments.models import PaymentInstrument, PaymentInstrumentStatus, Recurrent, RecurrentStatus
from users.models import User


SYMBOL_DISPLAY_LENGTH = 4


class UserRecurrentInfoGetterException(AppServiceException):
    """Exception for errors in getting recurrent subscription info."""


@dataclass
class UserRecurrentInfoGetter(BaseService):
    """Get active recurrent subscription info for user."""

    user: User

    def act(self) -> dict:
        recurrent = self.get_active_recurrent()
        payment_instrument = self.get_active_payment_instrument(recurrent)

        return {
            "product_name": recurrent.product.name,
            "amount": recurrent.amount,
            "next_charge_date": recurrent.next_charge_date or None,
            "card_mask": self.normalize_card_mask(payment_instrument.card_mask),
        }

    def get_active_recurrent(self) -> Recurrent:
        recurrent = Recurrent.objects.select_related("product", "payment_instrument").filter(user=self.user, status=RecurrentStatus.ACTIVE).first()
        if not recurrent:
            raise UserRecurrentInfoGetterException(_("User does not have an active recurrent subscription."))

        return recurrent

    def get_active_payment_instrument(self, recurrent: Recurrent) -> PaymentInstrument:
        payment_instrument = recurrent.payment_instrument
        if not payment_instrument or payment_instrument.status != PaymentInstrumentStatus.ACTIVE:
            raise UserRecurrentInfoGetterException(_("User does not have an active payment instrument."))

        return payment_instrument

    def normalize_card_mask(self, raw_mask: str) -> str:
        digits = "".join(ch for ch in raw_mask if ch.isdigit())
        if len(digits) < SYMBOL_DISPLAY_LENGTH:
            return "**** **** **** ****"

        return f"**** **** **** {digits[-SYMBOL_DISPLAY_LENGTH:]}"
