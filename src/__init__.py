# =========================================================
# src/__init__.py
# Defines the public interface for the 'src' package
# =========================================================

# Import src modules
from .ATM import ATM
from .BankService import BankService
from .DatabaseManager import DatabaseManager
from .ATM_Exceptions import (
    InsufficientFundsError,
    InvalidAmountError,
    TransactionLimitError,
    AuthError
)

# Define __all__
__all__ = [
    "BankService", "InsufficientFundsError", "InvalidAmountError",
    "TransactionLimitError", "AuthError", "DatabaseManager", "ATM"
]
