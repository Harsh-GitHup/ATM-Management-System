# =========================================================
# main.py
# Main execution file for the ATM Management System
# =========================================================

import os
import sys
import time
import hashlib
import mysql.connector
from datetime import date
from decimal import Decimal
from mysql.connector import Error

# ==========================================
# CONFIGURATION
# ==========================================
DB_CONFIG = {
    # Defaults to localhost if not set
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'password'),
    'database': os.getenv('DB_NAME', 'atm_db')
}

# Bank Rules
DAILY_WITHDRAWAL_LIMIT = Decimal('5000.00')
TRANSACTION_FEE = Decimal('2.00')  # Optional fee logic



# ==========================================
# CUSTOM EXCEPTIONS
# ==========================================
class ATMError(Exception):
    """Base class for other exceptions"""
    pass


class InsufficientFundsError(ATMError):
    pass


class InvalidAmountError(ATMError):
    pass


class AuthError(ATMError):
    pass


class TransactionLimitError(ATMError):
    pass



# ==========================================
# DATA ACCESS LAYER
# ==========================================
class DatabaseManager:
    """
    Handles raw database interactions.
    Implements the Context Manager pattern implicitly via methods
    to ensure connections are safe.
    """

    @staticmethod
    def get_connection():
        try:
            connection = mysql.connector.connect(**DB_CONFIG)
            if connection.is_connected():
                return connection
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            sys.exit(1)
    
    @staticmethod
    def execute_query(query, params=None):
        """Executes a query (INSERT, UPDATE, DELETE) and commits."""
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params or ())
            conn.commit()
            return cursor.lastrowid
        except Error as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def fetch_one(query, params=None):
        """Fetches a single row."""
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor(dictionary=True)  # Return results as dicts
        try:
            cursor.execute(query, params or ())
            return cursor.fetchone()
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def fetch_all(query, params=None):
        """Fetches all rows."""
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(query, params or ())
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()

# ==========================================
# BUSINESS LOGIC LAYER
# ==========================================


class BankService:
    """
    Contains all the business rules.
    It does not handle UI (print/input). It returns data or raises Exceptions.
    """

    @staticmethod
    def _hash_pin(pin):
        """Securely hashes the PIN using SHA-256."""
        return hashlib.sha256(pin.encode()).hexdigest()

    def create_account(self, name, pin):
        """Creates a User and an Account in an atomic transaction logic."""
        pin_hash = self._hash_pin(pin)

        # 1. Create User
        user_sql = "INSERT INTO users (name, pin_hash) VALUES (%s, %s)"
        user_id = DatabaseManager.execute_query(user_sql, (name, pin_hash))

        # 2. Create Account linked to User
        acct_sql = "INSERT INTO accounts (user_id, balance) VALUES (%s, %s)"
        acct_id = DatabaseManager.execute_query(acct_sql, (user_id, 0.00))

        return acct_id

    def login(self, account_id, pin):
        """Authenticates user. Returns user dict or raises AuthError."""
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
        return Decimal(result['balance'])

    def deposit(self, account_id, amount):
        if amount <= 0:
            raise InvalidAmountError("Deposit amount must be positive.")

        # Update Balance
        sql_update = "UPDATE accounts SET balance = balance + %s WHERE account_number = %s"
        DatabaseManager.execute_query(sql_update, (amount, account_id))

        # Log Transaction
        self._log_transaction(account_id, 'DEPOSIT', amount)
        return self.get_balance(account_id)

    def withdraw(self, account_id, amount):
        amount = Decimal(amount)
        if amount <= 0:
            raise InvalidAmountError("Amount must be positive.")

        # 1. Fetch current account state
        sql = "SELECT balance, daily_withdrawn_amount, last_withdrawal_date FROM accounts WHERE account_number = %s"
        acct = DatabaseManager.fetch_one(sql, (account_id,))

        current_balance = Decimal(acct['balance'])
        daily_total = Decimal(acct['daily_withdrawn_amount'])
        last_date = acct['last_withdrawal_date']
        today = date.today()

        # 2. Reset daily limit logic if new day
        if last_date != today:
            daily_total = Decimal(0)

        # 3. Validations
        if current_balance < amount:
            raise InsufficientFundsError(
                f"Insufficient funds. Balance: ${current_balance}")

        if (daily_total + amount) > DAILY_WITHDRAWAL_LIMIT:
            remaining = DAILY_WITHDRAWAL_LIMIT - daily_total
            raise TransactionLimitError(
                f"Daily limit exceeded. You can only withdraw ${remaining} more today.")

        # 4. Update Database
        new_daily = daily_total + amount
        sql_update = """
            UPDATE accounts 
            SET balance = balance - %s, 
                daily_withdrawn_amount = %s, 
                last_withdrawal_date = %s 
            WHERE account_number = %s
        """
        DatabaseManager.execute_query(
            sql_update, (amount, new_daily, today, account_id))

        # 5. Log
        self._log_transaction(account_id, 'WITHDRAWAL', amount)
        return self.get_balance(account_id)

    def transfer(self, from_acc_id, to_acc_id, amount):
        """
        Performs a transfer. 
        Note: In a real bank, this requires strict DB locking (ACID).
        Here we simulate the logic validation.
        """
        amount = Decimal(amount)

        # Validate Target Account
        target = DatabaseManager.fetch_one(
            "SELECT account_number FROM accounts WHERE account_number = %s", (to_acc_id,))
        if not target:
            raise InvalidAmountError("Target account does not exist.")

        if from_acc_id == to_acc_id:
            raise InvalidAmountError("Cannot transfer to self.")

        # Validate Funds (Re-using logic, but simpler)
        current_balance = self.get_balance(from_acc_id)
        if current_balance < amount:
            raise InsufficientFundsError("Insufficient funds for transfer.")

        # Execute Transfer
        # Deduct from Sender
        DatabaseManager.execute_query(
            "UPDATE accounts SET balance = balance - %s WHERE account_number = %s", (amount, from_acc_id))
        # Add to Receiver
        DatabaseManager.execute_query(
            "UPDATE accounts SET balance = balance + %s WHERE account_number = %s", (amount, to_acc_id))

        # Log (Only logging on sender's side for this simple demo, or log both)
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
        sql = "INSERT INTO transactions (account_id, transaction_type, amount, target_account_id) VALUES (%s, %s, %s, %s)"
        DatabaseManager.execute_query(sql, (account_id, type, amount, target))


# ==========================================
# PRESENTATION LAYER (CLI)
# ==========================================
class ATM:
    def __init__(self):
        self.service = BankService()
        self.current_user = None  # Stores session data

    def start(self):
        print("\n=== WELCOME TO PYTHON BANK ATM ===")
        while True:
            if not self.current_user:
                self._auth_menu()
            else:
                self._main_menu()

    def _auth_menu(self):
        print("\n1. Login")
        print("2. Create New Account")
        print("3. Exit")
        choice = input("Select option: ")

        try:
            if choice == '1':
                acc_id = input("Enter Account Number: ")
                pin = input("Enter PIN: ")
                self.current_user = self.service.login(acc_id, pin)
                print(f"\nWelcome back, {self.current_user['name']}!")
            elif choice == '2':
                name = input("Enter Full Name: ")
                pin = input("Set a 4-digit PIN: ")
                if len(pin) != 4 or not pin.isdigit():
                    print("Error: PIN must be 4 digits.")
                    return
                new_id = self.service.create_account(name, pin)
                print(f"Account created! Your Account Number is: {new_id}")
            elif choice == '3':
                print("Goodbye!")
                sys.exit()
            else:
                print("Invalid option.")
        except AuthError as e:
            print(f"Login Failed: {e}")
        except Exception as e:
            print(f"System Error: {e}")

    def _main_menu(self):
        print(f"\n--- Account: {self.current_user['account_number']} ---")
        print("1. Check Balance")
        print("2. Deposit")
        print("3. Withdraw")
        print("4. Transfer Funds")
        print("5. Transaction History")
        print("6. Logout")

        choice = input("Select option: ")

        try:
            if choice == '1':
                bal = self.service.get_balance(
                    self.current_user['account_number'])
                print(f"Current Balance: ${bal}")

            elif choice == '2':
                amt = float(input("Amount to deposit: "))
                new_bal = self.service.deposit(
                    self.current_user['account_number'], Decimal(amt))
                print(f"Deposit Successful. New Balance: ${new_bal}")

            elif choice == '3':
                amt = float(input("Amount to withdraw: "))
                new_bal = self.service.withdraw(
                    self.current_user['account_number'], Decimal(amt))
                print(f"Cash Dispensed. New Balance: ${new_bal}")

            elif choice == '4':
                target = input("Target Account Number: ")
                amt = float(input("Amount to transfer: "))
                new_bal = self.service.transfer(
                    self.current_user['account_number'], target, Decimal(amt))
                print(f"Transfer Sent. New Balance: ${new_bal}")

            elif choice == '5':
                history = self.service.get_transaction_history(
                    self.current_user['account_number'])
                print("\n--- Last 5 Transactions ---")
                print(f"{'TYPE':<12} | {'AMOUNT':<10} | {'DATE':<20}")
                print("-" * 45)
                for tx in history:
                    print(
                        f"{tx['transaction_type']:<12} | ${tx['amount']:<10} | {tx['timestamp']}")

            elif choice == '6':
                self.current_user = None
                print("Logged out successfully.")

            else:
                print("Invalid option.")

        except (InvalidAmountError, InsufficientFundsError, TransactionLimitError) as e:
            print(f"Transaction Failed: {e}")
        except ValueError:
            print("Error: Please enter valid numbers.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")


# ==========================================
# ENTRY POINT
# ==========================================
if __name__ == "__main__":
    # Ensure database is running before starting
    app = ATM()
    app.start()
