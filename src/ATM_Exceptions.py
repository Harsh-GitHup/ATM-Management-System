# =========================================================
# src/ATM_Exceptions.py
# Defines the Custom Exceptions for the 'src' package
# =========================================================

class ATMError(Exception):
    """Base exception for ATM-related errors."""
    pass


class AuthError(ATMError):
    """Raised when PIN or account is invalid."""

    def __init__(self, message="Invalid username or PIN."):
        self.message = message
        super().__init__(self.message)


class InsufficientFundsError(ATMError):
    """Raised when a withdrawal or transfer exceeds the balance."""

    def __init__(
        self,
        current_balance,
        amount_requested,
        message="Insufficient balance."
    ):
        self.current_balance = current_balance
        self.amount_requested = amount_requested
        self.message = (
            f"{message} Current balance: ${current_balance:.2f}. "
            f"Requested: ${amount_requested:.2f}."
        )
        super().__init__(self.message)


class TransactionLimitError(ATMError):
    """Raised when a transaction exceeds a predefined daily or per-transaction limit."""

    def __init__(self, limit_type, limit_amount, message="Transaction exceeds limit."):
        self.limit_type = limit_type
        self.limit_amount = limit_amount
        self.message = f"{message} {limit_type} limit is ${limit_amount:.2f}."
        super().__init__(self.message)


class InvalidAmountError(ATMError):
    """Raised for negative or zero amounts."""

    def __init__(self, message="Amount must be a positive value."):
        self.message = message
        super().__init__(self.message)
