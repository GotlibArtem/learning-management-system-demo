from dataclasses import dataclass

from django.db.transaction import atomic
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from app.exceptions import AppServiceException
from app.services import BaseService
from payments.models import PaymentInstrument, PaymentInstrumentStatus, Recurrent, RecurrentStatus
from users.models import User


class UserRecurrentCancellerException(AppServiceException):
    """Exception for errors during recurrent cancellation."""


@dataclass
class UserRecurrentCanceller(BaseService):
    """Cancel user's recurrent subscription and deactivate its payment instrument."""

    user: User

    def act(self) -> None:
        self.cancel_recurrent_subscription(self.recurrent, self.payment_instrument)

    @atomic
    def cancel_recurrent_subscription(self, recurrent: Recurrent, payment_instrument: PaymentInstrument) -> None:
        if payment_instrument.status == PaymentInstrumentStatus.ACTIVE:
            payment_instrument.status = PaymentInstrumentStatus.INACTIVE
            payment_instrument.save(update_fields=["status"])

        if recurrent.status == RecurrentStatus.ACTIVE:
            recurrent.status = RecurrentStatus.CANCELLED
            recurrent.save(update_fields=["status"])

    @cached_property
    def recurrent(self) -> Recurrent:
        recurrent = Recurrent.objects.select_related("product", "payment_instrument").filter(user=self.user).first()
        if not recurrent:
            raise UserRecurrentCancellerException(_("User does not have recurrent subscription."))

        return recurrent

    @cached_property
    def payment_instrument(self) -> PaymentInstrument:
        payment_instrument = self.recurrent.payment_instrument
        if not payment_instrument:
            raise UserRecurrentCancellerException(_("User does not have payment instrument."))

        return payment_instrument
