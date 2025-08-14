from datetime import time
from decimal import Decimal
from typing import Any

from django.core.serializers.json import DjangoJSONEncoder


class AppJSONEncoder(DjangoJSONEncoder):
    """Encoder that knows how to encode fucking time and decimals"""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, time):
            return str(obj)

        if isinstance(obj, Decimal):
            return str(obj)

        return super().default(obj)
