from collections.abc import Callable
from dataclasses import dataclass

from django.utils.functional import cached_property
from django.utils.translation import gettext as _

from app.exceptions import AppServiceException
from app.services import BaseService
from bonuses.models import BonusAccount, BonusTransaction, BonusTransactionType
from users.models import User
from users.services import UserCreator


class BonusTransactionCreatorException(AppServiceException):
    """Exception for bonus transaction creation errors."""


@dataclass
class BonusTransactionCreator(BaseService):
    email: str
    amount: int
    transaction_type: str
    reason: str = ""
    created_by: User | None = None

    def act(self) -> BonusAccount:
        self.create_transaction(self.account)

        return self.update_balance(self.account)

    def validate_user(self) -> None:
        if not self.user or not self.user.email:
            raise BonusTransactionCreatorException(_("User is required and must have an email."))

    def validate_amount(self) -> None:
        if self.amount <= 0:
            raise BonusTransactionCreatorException(_("Amount must be positive."))

    def validate_account(self) -> None:
        if not self.account.is_active:
            raise BonusTransactionCreatorException(_("Bonus account is not active."))

    def validate_balance(self) -> None:
        if self.is_spending and self.account.balance < self.amount:
            raise BonusTransactionCreatorException(_("Insufficient bonus balance."))

    def get_validators(self) -> list[Callable]:
        return [
            self.validate_user,
            self.validate_amount,
            self.validate_account,
            self.validate_balance,
        ]

    @cached_property
    def is_spending(self) -> bool:
        return self.transaction_type in [BonusTransactionType.SPENT, BonusTransactionType.ADMIN_SPENT]

    @cached_property
    def is_earning(self) -> bool:
        return self.transaction_type in [BonusTransactionType.EARNED, BonusTransactionType.ADMIN_EARNED]

    @cached_property
    def user(self) -> User:
        try:
            return User.objects.get(username=self.email)
        except User.DoesNotExist:
            if self.is_earning:
                return UserCreator(username=self.email)()
            raise BonusTransactionCreatorException(_("User matching query does not exist."))

    @cached_property
    def account(self) -> BonusAccount:
        account, _ = BonusAccount.objects.get_or_create(user=self.user)
        return account

    def create_transaction(self, account: BonusAccount) -> BonusTransaction:
        return BonusTransaction.objects.create(
            account=account,
            amount=-self.amount if self.is_spending else self.amount,
            transaction_type=self.transaction_type,
            reason=self.reason,
            created_by=self.created_by or self.user,
        )

    def update_balance(self, account: BonusAccount) -> BonusAccount:
        if self.is_spending:
            account.balance -= self.amount
        else:
            account.balance += self.amount
        account.save(update_fields=["balance"])

        return account
