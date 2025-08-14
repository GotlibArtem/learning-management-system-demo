from dataclasses import dataclass
from urllib.parse import urlencode, urljoin

from django.conf import settings

from app.services import BaseService
from products.models import Product


@dataclass
class PostCheckoutLinkGenerator(BaseService):
    username: str
    code: str | None
    product: Product

    def act(self) -> str:
        magic_link_page = "/order-checkedout"
        link_params = {
            "email": self.username,
            "product_type": self.product.product_type,
            "product_id": str(self.product.id),
        }
        if self.code is not None:
            link_params["code"] = self.code

        return urljoin(settings.ABSOLUTE_URL, f"{magic_link_page}?{urlencode(link_params)}")
