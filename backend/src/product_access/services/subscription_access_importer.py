from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

from django.utils import timezone
from django.utils.functional import cached_property

from app.services import BaseService
from product_access.models import ProductAccess
from products.models import Product
from users.models import User


@dataclass
class SubscriptionAccessImporter(BaseService):
    data: dict
    product: Product

    def act(self) -> ProductAccess | None:
        if self.data["Последний день подписки"].strip() == "":
            return None

        return ProductAccess.objects.update_or_create(
            user=self.user,
            product=self.product,
            defaults=dict(
                start_date=timezone.make_aware(datetime(2024, 1, 1)),
                end_date=timezone.make_aware(
                    datetime.combine(
                        datetime.fromisoformat(self.data["Последний день подписки"]).date(),
                        datetime.max.time(),
                    ),
                ),
                granted_at=timezone.make_aware(datetime(2024, 1, 1)),
                order_id=uuid4(),
            ),
        )[0]

    @cached_property
    def user(self) -> User:
        return User.objects.get(username=self.data["E-mail"].strip())
