# =========================================================
# src/BankService.py
# Business Logic Layer for the 'src' package
# =========================================================

import hashlib
import random
from datetime import date
from decimal import Decimal
from .DatabaseManager import DatabaseManager
from .ATM_Exceptions import (
    InsufficientFundsError,
    TransactionLimitError,
    InvalidAmountError,
    AuthError,
)

# --- Bank Rules ---
DAILY_WITHDRAWAL_LIMIT = Decimal('5000.00')
TRANSACTION_FEE = Decimal('2.00')   # Final logic kept for context
FEE_THRESHOLD = Decimal('100.00')   # Fees apply if withdrawing less than this


class BankService:
    """
    Contains all the business rules (limits, hashing, transfers).
    It communicates with the database layer but is unaware of the UI/CLI.
    """

    @staticmethod
    def _hash_pin(pin):
        """Securely hashes the PIN using SHA-256."""
        return hashlib.sha256(pin.encode()).hexdigest()

    @staticmethod
    def _generate_account_number():
        """Generates a unique 12-digit account number."""
        while True:
            # Generate a random 12-digit number (starts with non-zero digit)
            account_number = random.randint(100000000000, 999999999999)

            # Check if this account number already exists
            sql = "SELECT account_number FROM accounts WHERE account_number = %s"
            existing = DatabaseManager.fetch_one(sql, (account_number,))

            if not existing:
                return account_number

    def create_account(self, name, pin):
        """Creates a User and an Account atomically (conceptually)."""
        pin_hash = self._hash_pin(pin)
        user_sql = "INSERT INTO users (name, pin_hash) VALUES (%s, %s)"
        user_id = DatabaseManager.execute_query(user_sql, name, pin_hash)

        # Generate unique 12-digit account number
        account_number = self._generate_account_number()

        acct_sql = """
        INSERT INTO accounts (account_number, user_id, balance) VALUES (%s, %s, %s)
        """
        DatabaseManager.execute_query(acct_sql, account_number, user_id, 0.00)
        return account_number

    def login(self, account_id, pin):
        """Authenticates user."""
        sql = """
            SELECT u.name, a.account_number, a.balance, u.pin_hash 
            FROM accounts a 
            JOIN users u ON a.user_id = u.user_id 
            WHERE a.account_number = %s
        """
        data = DatabaseManager.fetch_one(sql, (account_id,))
        if not data:
            raise AuthError("Account not found.")
        if data['pin_hash'] != self._hash_pin(pin):
            raise AuthError("Invalid PIN.")
        return data

    def get_balance(self, account_id):
        sql = "SELECT balance FROM accounts WHERE account_number = %s"
        result = DatabaseManager.fetch_one(sql, (account_id,))
        # Handle case where account exists but balance might be null/error (defensive)
        if not result:
            raise AuthError("Account not found.")
        return Decimal(result['balance'])

    def deposit(self, account_id, amount):
        if amount <= 0:
            raise InvalidAmountError("Deposit amount must be positive.")

        sql_update = """
        UPDATE accounts 
        SET balance = balance + %s 
        WHERE account_number = %s
        """
        DatabaseManager.execute_query(sql_update, amount, account_id)

        self._log_transaction(account_id, 'DEPOSIT', amount)
        return self.get_balance(account_id)

    def withdraw(self, account_id, amount):
        amount = Decimal(amount)
        if amount <= 0:
            raise InvalidAmountError("Amount must be positive.")

        # --- FEE LOGIC ---
        fee = Decimal('0.00')
        if amount < FEE_THRESHOLD:
            fee = TRANSACTION_FEE

        total_deduction = amount + fee

        # 1. Fetch current account state
        sql = """
        SELECT balance, daily_withdrawn_amount, last_withdrawal_date 
        FROM accounts 
        WHERE account_number = %s
        """
        acct = DatabaseManager.fetch_one(sql, (account_id,))

        current_balance = Decimal(acct['balance'])
        daily_total = Decimal(acct['daily_withdrawn_amount'])
        last_date = acct['last_withdrawal_date']
        today = date.today()

        # 2. Reset daily limit logic if new day
        if last_date != today:
            daily_total = Decimal(0)

        # 3. Validations (Check Balance and Daily Limit)
        if current_balance < total_deduction:
            raise InsufficientFundsError(
                current_balance, total_deduction,
                message=(
                    f"Insufficient funds (incl. ${fee} fee). "
                    f"Balance: ${current_balance}")
            )

        if (daily_total + amount) > DAILY_WITHDRAWAL_LIMIT:
            remaining = DAILY_WITHDRAWAL_LIMIT - daily_total
            raise TransactionLimitError(
                "Daily Withdrawal", DAILY_WITHDRAWAL_LIMIT,
                message=(
                    "Daily limit exceeded. You can only "
                    f"withdraw ${remaining:.2f} more today.")
            )

        # 4. Use atomic SQL update logic to Update Database
        if last_date != today:
            # Reset daily amount and add current withdrawal
            sql_update = """
                UPDATE accounts 
                SET balance = balance - %s, 
                    daily_withdrawn_amount = %s, 
                    last_withdrawal_date = %s 
                WHERE account_number = %s
            """
            DatabaseManager.execute_query(
                sql_update, total_deduction, amount, today, account_id)

        else:
            # Add to existing daily amount (Atomic update)
            sql_update = """
                UPDATE accounts 
                SET balance = balance - %s, 
                    daily_withdrawn_amount = daily_withdrawn_amount + %s 
                WHERE account_number = %s
                """
            # Note: We pass the raw 'amount' for daily_withdrawn_amount.
            # Total deduction is from balance.
            DatabaseManager.execute_query(
                sql_update, total_deduction, amount, account_id)

        # 5. Log
        self._log_transaction(account_id, 'WITHDRAWAL', amount)
        if fee > 0:
            # Log the fee separately
            self._log_transaction(account_id, 'FEE', fee)

        return self.get_balance(account_id)

    def transfer(self, from_acc_id, to_acc_id, amount):
        amount = Decimal(amount)

        target = DatabaseManager.fetch_one(
            "SELECT account_number FROM accounts WHERE account_number = %s",
            (to_acc_id,))
        if not target:
            raise InvalidAmountError("Target account does not exist.")

        if str(from_acc_id) == str(to_acc_id):
            raise InvalidAmountError("Can't transfer to self.")

        current_balance = self.get_balance(from_acc_id)
        if current_balance < amount:
            raise InsufficientFundsError(
                current_balance, amount,
                message="Insufficient funds for transfer."
            )

        # Execute Transfer
        # (This is where ACID transaction logic should be enforced in a real system)
        DatabaseManager.execute_query(
            "UPDATE accounts SET balance = balance - %s WHERE account_number = %s",
            amount, from_acc_id)
        DatabaseManager.execute_query(
            "UPDATE accounts SET balance = balance + %s WHERE account_number = %s",
            amount, to_acc_id)

        self._log_transaction(from_acc_id, 'TRANSFER', amount, to_acc_id)

        return self.get_balance(from_acc_id)

    def get_transaction_history(self, account_id):
        sql = """
            SELECT transaction_type, amount, timestamp, target_account_id 
            FROM transactions 
            WHERE account_id = %s 
            ORDER BY timestamp DESC LIMIT 5
        """
        return DatabaseManager.fetch_all(sql, (account_id,))

    def _log_transaction(self, account_id, type, amount, target=None):
        sql = """ INSERT INTO transactions (
            transaction_type, amount, account_id, target_account_id
            ) VALUES (%s, %s, %s, %s)
        """
        DatabaseManager.execute_query(sql, type, amount, account_id, target)
