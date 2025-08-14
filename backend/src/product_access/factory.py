import uuid
from typing import Any

from app.testing import register
from app.testing.types import FactoryProtocol
from product_access.models import ProductAccess


@register
def product_access(self: FactoryProtocol, **kwargs: Any) -> ProductAccess:
    kwargs.setdefault("shop_id", str(uuid.uuid4()))
    return self.mixer.blend("product_access.ProductAccess", **kwargs)
