import csv
from pathlib import Path

from django.core.management.base import BaseCommand

from bonuses.models import BonusAccount, BonusTransactionType
from bonuses.services import BonusTransactionCreator, BonusTransactionCreatorException
from users.models import User


class Command(BaseCommand):
    """Import bonus balances from a CSV file and update them via the BonusTransactionCreator service."""

    help = "Import bonus balances from CSV and update them via service, creating income and spending transactions."

    MAX_AMOUNT = 2_000_000_000
    LOG_EVERY = 100  # Log progress every N users

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str, help="Path to the input CSV file")
        parser.add_argument("--output", type=str, default="failed_imports.csv", help="Path to the CSV file with failed rows")

    def handle(self, *args, **options):
        csv_path = Path(options["csv_path"])
        failed_path = Path(options["output"])

        failed_rows = []
        total_records = self.get_total_records(csv_path)
        admin_user = self.get_admin_user()
        if not admin_user:
            return

        processed = 0

        with csv_path.open(newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
                processed += 1

                if processed % self.LOG_EVERY == 0 or processed == total_records:
                    self.stdout.write(f"Progress: {processed}/{total_records} records processed.")

                if not self.process_row(row, admin_user):
                    failed_rows.append(row)

        self.save_failed_rows(failed_rows, reader.fieldnames, failed_path)

    def get_total_records(self, csv_path: Path) -> int:
        with csv_path.open(newline="", encoding="utf-8") as csvfile:
            return sum(1 for _ in csvfile) - 1

    def get_admin_user(self) -> User | None:
        try:
            return User.objects.get(username="admin")
        except User.DoesNotExist:
            self.stderr.write("Admin user not found. Process aborted.")
            return None

    def process_row(self, row: dict, admin_user: User) -> bool:
        email = row["email пользователя"].strip().lower()

        try:
            income = min(int(row["Приход"]), self.MAX_AMOUNT)
            spending = abs(min(int(row["Расход"]), self.MAX_AMOUNT))
            expected_balance = max(min(int(row["Сальдо"]), self.MAX_AMOUNT), -self.MAX_AMOUNT)
        except ValueError:
            self.stderr.write(f"Failed to parse values for {email}. Row skipped.")
            return False

        if income == 0 and spending == 0 and expected_balance == 0:
            return True  # Skip empty rows silently

        safe_income = min(income, self.MAX_AMOUNT)

        try:
            if safe_income > 0:
                self.create_transaction(
                    email,
                    safe_income,
                    BonusTransactionType.ADMIN_EARNED,
                    "Перенос истории транзакции (начисление) из getcourse",
                    admin_user,
                )

            if expected_balance < 0:
                # Если сальдо отрицательное, списываем всё начисленное, чтобы обнулить
                spending_to_apply = safe_income
            else:
                # Если сальдо положительное или нулевое, списание по фактическому значению
                spending_to_apply = min(spending, self.MAX_AMOUNT)

            if spending_to_apply > 0:
                self.create_transaction(
                    email,
                    spending_to_apply,
                    BonusTransactionType.ADMIN_SPENT,
                    "Перенос истории транзакции (списание) из getcourse",
                    admin_user,
                )

            return self.check_and_correct_balance(email, expected_balance, admin_user)
        except BonusTransactionCreatorException as e:
            self.stderr.write(f"Failed to update balance for {email}: {e!s}")
            return False

    def create_transaction(self, email: str, amount: int, transaction_type: str, reason: str, admin_user: User) -> None:
        safe_amount = min(amount, self.MAX_AMOUNT)

        BonusTransactionCreator(
            email=email,
            amount=safe_amount,
            transaction_type=transaction_type,
            reason=reason,
            created_by=admin_user,
        )()

    def check_and_correct_balance(self, email: str, expected_balance: int, admin_user: User) -> bool:
        try:
            account = BonusAccount.objects.get(user__username=email)
        except BonusAccount.DoesNotExist:
            self.stderr.write(f"Bonus account not found for {email}")
            return False

        if account.balance == expected_balance:
            return True

        correction_amount = abs(account.balance - expected_balance)
        safe_correction = min(correction_amount, self.MAX_AMOUNT)

        if account.balance > expected_balance:
            correction_type = BonusTransactionType.ADMIN_SPENT
            correction_reason = "Корректировка бонусного баланса (снижение) по getcourse"
        else:
            correction_type = BonusTransactionType.ADMIN_EARNED
            correction_reason = "Корректировка бонусного баланса (увеличение) по getcourse"

        self.create_transaction(email, safe_correction, correction_type, correction_reason, admin_user)
        return True

    def save_failed_rows(self, failed_rows: list, fieldnames: list, failed_path: Path) -> None:
        if not failed_rows:
            self.stdout.write("All records have been successfully processed.")
            return

        with failed_path.open("w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(failed_rows)

        self.stdout.write(f"Some records failed. Unprocessed rows have been saved to {failed_path}.")
