import pytest

from bonuses.models import BonusAccount
from bonuses.services.bonus_account_getter import BonusAccountGetter, BonusAccountGetterException


pytestmark = [
    pytest.mark.django_db,
]


def test_gets_existing_active_account(bonus_account):
    result = BonusAccountGetter(email=bonus_account.user.email)()

    assert result == bonus_account
    assert result.is_active
    assert result.balance == bonus_account.balance


def test_creates_account_if_not_exists(user):
    assert not BonusAccount.objects.filter(user=user).exists()

    result = BonusAccountGetter(email=user.email)()

    assert isinstance(result, BonusAccount)
    assert result.user == user
    assert result.is_active
    assert result.balance == 0


def test_raises_if_account_inactive(bonus_account):
    bonus_account.is_active = False
    bonus_account.save()

    with pytest.raises(BonusAccountGetterException, match="Bonus account is not active."):
        BonusAccountGetter(email=bonus_account.user.email)()


def test_raises_if_user_not_found():
    with pytest.raises(BonusAccountGetterException, match="User matching query does not exist."):
        BonusAccountGetter(email="notfound@example.com")()
