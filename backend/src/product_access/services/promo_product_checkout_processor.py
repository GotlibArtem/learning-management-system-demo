from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.db.transaction import atomic, on_commit
from django.utils.functional import cached_property
from django.utils.translation import gettext as _

from a12n.models import PasswordlessEmailAuthCode
from app.exceptions import AppServiceException
from app.services import BaseService
from product_access.models import ProductAccess
from product_access.services.post_checkout_link_generator import PostCheckoutLinkGenerator
from product_access.services.timed_product_access_provider import TimedProductAccessProvider
from products.models import Product
from users.models import User
from users.services import UserEditor


DEFAULT_PROMO_LIFETIME_DAYS = 1


class PromoProductCheckoutProcessorException(AppServiceException):
    """Raise if an error occurs in promo product checkout processor."""


@dataclass
class PromoProductCheckoutProcessor(BaseService):
    """
    Process checkout request to the product for lifetime from the moment of promo_event from the lms shop.
    """

    checkout_event: dict

    def act(self) -> str:
        with atomic():
            user = self.user_with_creation_state[0]

            if self._has_active_subscription(user):
                raise PromoProductCheckoutProcessorException(_("You already have a subscription, share this page with others."))

            start_at = self.checkout_event["event_time"]
            end_at = start_at + timedelta(days=(self.product.lifetime if self.product.lifetime else DEFAULT_PROMO_LIFETIME_DAYS))
            order_id = f"promo-{self.checkout_event['event_id']}"

            product_access = TimedProductAccessProvider(
                user=user,
                product=self.product,
                start_at=start_at,
                end_at=end_at,
                order_id=order_id,
                access_granted_time=self.checkout_event["event_time"],
            )()

        return self.redirect_url

    def _has_active_subscription(self, user: User) -> bool:
        return ProductAccess.objects.active_for_user(user).filter(product__product_type="subscription").exists()

    @cached_property
    def product(self) -> Product:
        try:
            return Product.objects.get(shop_id=settings.PROMO_PRODUCT_SHOP_ID)
        except Product.DoesNotExist:
            raise PromoProductCheckoutProcessorException(_("Promo product not found."))

    @cached_property
    def user_with_creation_state(self) -> tuple[User, bool]:
        user_data = self.checkout_event["data"]["user"]
        return UserEditor(username=user_data["username"])()

    @cached_property
    def auth_code(self) -> PasswordlessEmailAuthCode:
        return PasswordlessEmailAuthCode.objects.create(user=self.user_with_creation_state[0])

    @cached_property
    def redirect_url(self) -> str:
        user, _ = self.user_with_creation_state
        return PostCheckoutLinkGenerator(
            product=self.product,
            code=self.auth_code.code,
            username=user.username,
        )()
