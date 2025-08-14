import hashlib
from dataclasses import dataclass
from typing import Any

from django.conf import settings

from app.services import BaseService


@dataclass
class TinkoffTokenGenerator(BaseService):
    """Generate SHA256 token for Tinkoff API requests."""

    payload: dict[str, Any]

    def act(self) -> str:
        return self.generate()

    def generate(self) -> str:
        flat_fields = {k: str(v).lower() if isinstance(v, bool) else str(v) for k, v in self.payload.items() if not isinstance(v, dict | list)}

        flat_fields["Password"] = settings.TINKOFF_TERMINAL_PASSWORD

        token_string = "".join(flat_fields[k] for k in sorted(flat_fields))

        return hashlib.sha256(token_string.encode("utf-8")).hexdigest()
