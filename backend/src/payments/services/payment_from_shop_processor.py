from dataclasses import dataclass
from datetime import datetime, timedelta

from django.db.transaction import atomic, on_commit
from django.utils.functional import cached_property
from django.utils.translation import gettext as _

from app.exceptions import AppServiceException
from app.services import BaseService
from mindbox.tasks import update_or_create_recurrent_order
from payments.models import Payment, PaymentInstrument, PaymentInstrumentStatus, Recurrent, RecurrentChargeAttempt, RecurrentChargeStatus
from products.models import Product
from users.models import User
from users.services import UserEditor


class PaymentFromShopProcessorException(AppServiceException):
    """Exception for errors in PaymentFromShopProcessor."""


@dataclass
class PaymentFromShopProcessor(BaseService):
    payment_data: dict

    @atomic
    def act(self) -> Payment:
        user = self.user_with_creation_state[0]
        try:
            payment, created = Payment.objects.update_or_create(
                external_payment_id=self.payment_data["payment_id"],
                order_id=self.payment_data["order_id"],
                user=user,
                product=self.product,
                source=self.payment_data["source"],
                provider=self.payment_data["provider"],
                payment_method=self.payment_data["payment_method"],
                defaults=dict(
                    is_recurrent=self.payment_data.get("is_recurrent"),
                    status=self.payment_data["status"],
                    paid_at=self.payment_data["paid_at"],
                    order_price=self.payment_data["order_price"],
                    total_price=self.payment_data["total_price"],
                    amount=self.payment_data["total_price"],
                    discount_price=self.payment_data.get("discount_price") or 0,
                    bonus_applied=self.payment_data.get("bonus_applied") or 0,
                    promo_code=self.payment_data.get("promo_code") or "",
                    provider_response=self.payment_data.get("provider_response"),
                ),
            )

            if recurrent := self.payment_data.get("recurrent"):
                self.create_or_update_recurrent(payment, recurrent)

            return payment
        except Exception as e:
            raise PaymentFromShopProcessorException(
                _("Unexpected error during payment import: {error}").format(error=str(e)),
            ) from e

    @cached_property
    def user_with_creation_state(self) -> tuple[User, bool]:
        user_data = self.payment_data["user"]
        return UserEditor(
            username=user_data["email"],
            phone=user_data["phone"],
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            rhash=user_data.get("rhash"),
        )()

    @cached_property
    def product(self) -> Product:

        product_data = self.payment_data["product"]
        if not product_data["lms_id"]:
            product, created = Product.objects.get_or_create(
                shop_id=product_data["shop_id"],
                defaults={
                    "name": product_data["name"],
                },
            )
            return product

        try:
            product = Product.objects.get(id=product_data["lms_id"])
            product.shop_id = product_data["shop_id"]
            product.save(update_fields=["shop_id", "modified"])
            return product
        except Product.DoesNotExist:
            raise PaymentFromShopProcessorException(_("Product {product} does not exist").format(product=product_data["lms_id"]))

    def create_or_update_recurrent(self, payment: Payment, recurrent_data: dict) -> Recurrent:
        instrument = self.create_or_update_payment_instrument(payment)

        try:
            recurrent, created = Recurrent.objects.update_or_create(
                user=payment.user,
                product=payment.product,
                defaults=dict(
                    payment_instrument=instrument,
                    status=recurrent_data["status"],
                    amount=recurrent_data.get("amount", 0),
                    next_charge_date=recurrent_data.get("next_charge_date") or self.get_next_charge_date(payment),
                    last_attempt_charge_date=recurrent_data.get("last_attempt_charge_date"),
                    last_attempt_charge_status=recurrent_data.get("last_attempt_charge_status") or "",
                ),
            )

            if payment.recurrent != recurrent:
                payment.recurrent = recurrent
                payment.save(update_fields=["recurrent"])

            attempts = recurrent_data.get("attempts_charge") or []
            raw_attempts = recurrent_data.get("attempts_charge_raw") or []
            if attempts:
                self.create_first_charge_attempt(
                    payment,
                    recurrent,
                    attempts[0],
                    raw_data=raw_attempts[0] if len(raw_attempts) > 0 else {},
                )

            on_commit(lambda: update_or_create_recurrent_order.delay(str(payment.user.id), str(recurrent.id)))  # type: ignore[union-attr]

            return recurrent
        except Exception as e:
            raise PaymentFromShopProcessorException(
                _("Failed to create or update recurrent subscription: {error}").format(error=str(e)),
            ) from e

    def create_or_update_payment_instrument(self, payment: Payment) -> PaymentInstrument | None:
        attempts = self.payment_data.get("recurrent", {}).get("attempts_charge") or []
        if not attempts:
            return None

        attempt = attempts[0]

        instrument, created = PaymentInstrument.objects.update_or_create(
            user=payment.user,
            provider=self.payment_data["recurrent"]["provider"],
            payment_method=self.payment_data["recurrent"]["charge_method"],
            rebill_id=attempt.get("rebill_id") or "",
            defaults=dict(
                card_mask=attempt.get("pan") or "",
                exp_date=attempt.get("exp_date") or "",
                card_id=attempt.get("card_id") or "",
                status=PaymentInstrumentStatus.ACTIVE,
                token=attempt.get("token") or "",
            ),
        )

        if instrument and payment.payment_instrument != instrument:
            payment.payment_instrument = instrument
            payment.save(update_fields=["payment_instrument"])

        return instrument

    def create_first_charge_attempt(
        self,
        payment: Payment,
        recurrent: Recurrent,
        attempt_data: dict,
        raw_data: dict,
    ) -> None:
        RecurrentChargeAttempt.objects.create(
            recurrent=recurrent,
            payment=payment,
            status=RecurrentChargeStatus.SUCCESS if attempt_data.get("success") else RecurrentChargeStatus.FAIL,
            amount=attempt_data.get("amount") or payment.amount,
            currency=attempt_data.get("currency") or "rub",
            error_code=attempt_data.get("error_code") or "",
            error_message="",
            external_payment_id=attempt_data.get("payment_id") or "",
            provider_response=raw_data,
        )

    def get_next_charge_date(self, payment: Payment) -> datetime | None:
        if not payment.paid_at or not payment.product or not payment.product.lifetime:
            return None

        return payment.paid_at + timedelta(days=payment.product.lifetime)
