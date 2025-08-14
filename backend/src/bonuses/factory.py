from typing import Any

from app.testing import register
from app.testing.types import FactoryProtocol
from bonuses.models import BonusAccount, BonusTransaction, BonusTransactionType


@register
def bonus_account(self: FactoryProtocol, **kwargs: Any) -> BonusAccount:
    kwargs.setdefault("user", self.user())  # type: ignore
    kwargs.setdefault("balance", 100)
    kwargs.setdefault("is_active", True)
    return self.mixer.blend("bonuses.BonusAccount", **kwargs)


@register
def bonus_transaction(self: FactoryProtocol, **kwargs: Any) -> BonusTransaction:
    kwargs.setdefault("account", self.bonus_account())  # type: ignore
    kwargs.setdefault("amount", 10)
    kwargs.setdefault("transaction_type", BonusTransactionType.EARNED)
    kwargs.setdefault("reason", "Test reason")
    kwargs.setdefault("created_by", self.user())  # type: ignore
    return self.mixer.blend("bonuses.BonusTransaction", **kwargs)
