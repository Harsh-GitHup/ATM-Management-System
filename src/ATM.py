# =========================================================
# src/ATM.py
# Presentation Layer for the 'src' package
# =========================================================

import sys
from decimal import Decimal, InvalidOperation

# Import from the current package modules
from .BankService import BankService
from .ATM_Exceptions import (
    AuthError,
    InvalidAmountError,
    InsufficientFundsError,
    TransactionLimitError
)

class ATM:
    """
    The Presentation Layer. Handles all user input and output.
    It relies entirely on BankService for business logic.
    """

    def __init__(self):
        self.service = BankService()
        self.current_user = None  # Stores session data

    def start(self):
        print("\n=== WELCOME TO PYTHON BANK ATM ===")
        # Main loop
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
            print(f"System Error: An unexpected error occurred: {e}")

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
            current_account_id = self.current_user['account_number']

            if choice == '1':
                bal = self.service.get_balance(current_account_id)
                print(f"Current Balance: ${bal}")

            elif choice == '2':
                amt = input("Amount to deposit: ")
                new_bal = self.service.deposit(
                    current_account_id, Decimal(amt))
                print(f"Deposit Successful. Balance: ${new_bal}")

            elif choice == '3':
                amt = input("Amount to withdraw: ")
                new_bal = self.service.withdraw(
                    current_account_id, Decimal(amt))
                print(f"Cash Dispensed. Balance: ${new_bal}")

            elif choice == '4':
                target = input("Target Account Number: ")
                amt = input("Amount to transfer: ")
                new_bal = self.service.transfer(
                    current_account_id, target, Decimal(amt))
                print(f"Transfer Sent. Balance: ${new_bal}")

            elif choice == '5':
                history = self.service.get_transaction_history(
                    current_account_id)
                print("\n--- Last 5 Transactions ---")
                print(f"{'TYPE':<12} | {'AMOUNT':<10} | {'DATE':<20}")
                print("-" * 45)
                for tx in history:
                    print(
                        f"{tx['transaction_type']:<12} | "
                        f"${tx['amount']:<10} | {tx['timestamp']}"
                    )

            elif choice == '6':
                self.current_user = None
                print("Logged out successfully.")

            else:
                print("Invalid option.")

        # Centralized exception handling for clean error messages
        except (InvalidAmountError, InsufficientFundsError, TransactionLimitError) as e:
            print(f"Transaction Failed: {e}")
        except (ValueError, InvalidOperation):
            print("Error: Please enter valid numeric data.")
        except Exception as e:
            print(f"An unexpected error occurred during operation: {e}")
