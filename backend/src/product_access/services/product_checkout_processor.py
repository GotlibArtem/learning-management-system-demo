from dataclasses import dataclass

from django.db.transaction import atomic, on_commit
from django.utils.functional import cached_property
from django.utils.translation import gettext as _

from a12n.models import PasswordlessEmailAuthCode
from app.exceptions import AppServiceException
from app.services import BaseService
from product_access.services.post_checkout_link_generator import PostCheckoutLinkGenerator
from product_access.services.product_access_provider import ProductAccessProvider
from products.models import Product
from users.models import User
from users.services import UserEditor


class ProductCheckoutProcessorException(AppServiceException):
    """
    Raise for any product processing exception
    """


@dataclass
class ProductCheckoutProcessor(BaseService):
    """
    Process checkout request from the lms shop
    """

    checkout_event: dict

    def act(self) -> str:
        with atomic():
            user = self.user_with_creation_state[0]
            product_access = ProductAccessProvider(
                user=user,
                product=self.product,
                start_date=self.checkout_data["start_date"],
                end_date=self.checkout_data["end_date"],
                order_id=self.checkout_data["order_id"],
                access_granted_time=self.checkout_event["event_time"],
            )()

        return self.redirect_url

    @cached_property
    def product(self) -> Product:
        product_data = self.checkout_data["product"]
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
            raise ProductCheckoutProcessorException(_("Product {product} does not exist").format(product=product_data["lms_id"]))

    @cached_property
    def user_with_creation_state(self) -> tuple[User, bool]:
        user_data = self.checkout_data["user"]
        return UserEditor(
            username=user_data["username"],
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            rhash=user_data.get("rhash"),
        )()

    @cached_property
    def auth_code(self) -> PasswordlessEmailAuthCode:
        return PasswordlessEmailAuthCode.objects.create(user=self.user_with_creation_state[0])

    @cached_property
    def redirect_url(self) -> str:
        user, user_created = self.user_with_creation_state
        return PostCheckoutLinkGenerator(
            product=self.product,
            code=self.auth_code.code if user_created else None,
            username=user.username,
        )()

    @property
    def checkout_data(self) -> dict:
        return self.checkout_event["data"]
