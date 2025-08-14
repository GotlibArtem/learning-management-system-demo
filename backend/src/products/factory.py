from typing import Any

from app.testing import register
from app.testing.types import FactoryProtocol
from products.models import Product


@register
def product(self: FactoryProtocol, **kwargs: Any) -> Product:
    return self.mixer.blend("products.Product", **kwargs)
