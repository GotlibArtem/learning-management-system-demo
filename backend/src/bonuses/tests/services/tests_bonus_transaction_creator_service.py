import pytest

from bonuses.models import BonusTransaction, BonusTransactionType
from bonuses.services import BonusTransactionCreator, BonusTransactionCreatorException


pytestmark = [
    pytest.mark.django_db,
]


def test_earn_bonuses_creates_transaction_and_increases_balance(bonus_account):
    user = bonus_account.user

    creator = BonusTransactionCreator(
        email=user.email,
        amount=50,
        transaction_type=BonusTransactionType.EARNED,
        reason="Test earn",
    )
    account = creator()

    assert BonusTransaction.objects.filter(account=account, amount=50, transaction_type=BonusTransactionType.EARNED).exists()
    assert account.balance == 150


def test_spend_bonuses_creates_transaction_and_decreases_balance(bonus_account):
    user = bonus_account.user
    account = user.bonus_account
    account.balance = 100
    account.save()

    creator = BonusTransactionCreator(
        email=user.email,
        amount=30,
        transaction_type=BonusTransactionType.SPENT,
        reason="Test spend",
    )
    updated_account = creator()

    assert BonusTransaction.objects.filter(account=updated_account, amount=-30, transaction_type=BonusTransactionType.SPENT).exists()
    assert updated_account.balance == 70


def test_spend_bonuses_raises_if_not_enough_balance(bonus_account):
    user = bonus_account.user
    account = user.bonus_account
    account.balance = 10
    account.save()

    creator = BonusTransactionCreator(
        email=user.email,
        amount=50,
        transaction_type=BonusTransactionType.SPENT,
        reason="Test spend fail",
    )

    with pytest.raises(BonusTransactionCreatorException, match="Insufficient bonus balance."):
        creator()


def test_raises_if_account_inactive(bonus_account):
    user = bonus_account.user
    account = user.bonus_account
    account.is_active = False
    account.save()

    creator = BonusTransactionCreator(
        email=user.email,
        amount=10,
        transaction_type=BonusTransactionType.EARNED,
        reason="Inactive account",
    )

    with pytest.raises(BonusTransactionCreatorException, match="Bonus account is not active."):
        creator()


def test_raises_if_amount_not_positive(bonus_account):
    user = bonus_account.user

    creator = BonusTransactionCreator(
        email=user.email,
        amount=0,
        transaction_type=BonusTransactionType.EARNED,
        reason="Zero amount",
    )

    with pytest.raises(BonusTransactionCreatorException, match="Amount must be positive."):
        creator()


def test_bonus_transaction_fixture_usage(bonus_transaction):
    assert bonus_transaction.account is not None
    assert bonus_transaction.amount == 10
    assert bonus_transaction.transaction_type is not None
    assert bonus_transaction.created_by is not None
