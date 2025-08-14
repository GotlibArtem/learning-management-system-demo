import pytest

from app.testing.factory import FixtureFactory
from bonuses.models import BonusAccount, BonusTransaction


@pytest.fixture
def bonus_account(factory: FixtureFactory) -> BonusAccount:
    return factory.bonus_account()


@pytest.fixture
def bonus_transaction(factory: FixtureFactory) -> BonusTransaction:
    return factory.bonus_transaction()
