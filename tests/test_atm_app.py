# =========================================================
# tests/test_atm_app.py
# Defines the Unit Tests for the ATM Management System in 'tests' package
# =========================================================

import pytest
from decimal import Decimal
from unittest.mock import patch
from datetime import date

# FIX: Import from src package
from src.BankService import BankService
from src.ATM_Exceptions import (
    InsufficientFundsError,
    TransactionLimitError,
    InvalidAmountError,
    AuthError,
)


# -- TEST FIXTURES --
@pytest.fixture
def service():
    """Returns a fresh instance of BankService for each test."""
    return BankService()


# -- UNIT TESTS --
def test_hash_pin_security(service):
    pin = "1234"
    hashed = service._hash_pin(pin)
    assert hashed != pin
    assert len(hashed) == 64


# Patch the DatabaseManager from where it is imported in BankService
@patch('src.BankService.DatabaseManager')
def test_login_success(mock_db, service):
    hashed_pin = service._hash_pin("1234")
    mock_db.fetch_one.return_value = {
        'name': 'Alice',
        'account_number': 101,
        'balance': 5000.00,
        'pin_hash': hashed_pin
    }
    user = service.login(101, "1234")
    assert user['name'] == 'Alice'
    with pytest.raises(AuthError):
        service.login(101, "wrong pin")


@patch('src.BankService.DatabaseManager')
def test_deposit_positive(mock_db, service):
    mock_db.fetch_one.return_value = {'balance': 150.00}
    new_balance = service.deposit(101, 50.00)
    assert new_balance == Decimal('150.00')


@patch('src.BankService.DatabaseManager')
def test_withdraw_success(mock_db, service):
    mock_db.fetch_one.side_effect = [
        {'balance': 1000.00, 'daily_withdrawn_amount': 0.00,
            'last_withdrawal_date': date.today()},
        {'balance': 900.00}
    ]
    new_balance = service.withdraw(101, 100.00)
    assert new_balance == Decimal('900.00')
    with pytest.raises(InvalidAmountError):
        service.withdraw(101, -100.00)


@patch('src.BankService.DatabaseManager')
def test_withdraw_insufficient_funds(mock_db, service):
    mock_db.fetch_one.return_value = {
        'balance': 50.00,
        'daily_withdrawn_amount': 0.00,
        'last_withdrawal_date': date.today()
    }
    with pytest.raises(InsufficientFundsError):
        service.withdraw(101, 100.00)


# Other tests need to be updated to patch the correct path
@patch('src.BankService.DatabaseManager')
def test_login_success_ok(mock_db, service):
    """Test successful login with mocked DB response."""
    hashed_pin = service._hash_pin("1234")
    mock_user_data = {
        'name': 'Alice',
        'account_number': 101,
        'balance': 5000.00,
        'pin_hash': hashed_pin
    }
    mock_db.fetch_one.return_value = mock_user_data
    user = service.login(101, "1234")
    assert user['name'] == 'Alice'
    mock_db.fetch_one.assert_called_once()
    with pytest.raises(AuthError):
        service.login(101, "wrong pin")


# Example of a corrected limit test:
@patch('src.BankService.DatabaseManager')
def test_withdraw_daily_limit_exceeded(mock_db, service):
    """Test that daily limits are enforced."""
    mock_db.fetch_one.return_value = {
        'balance': 10000.00,
        'daily_withdrawn_amount': 4900.00,  # Limit is 5000
        'last_withdrawal_date': date.today()
    }
    # User tries to withdraw 200 (4900 + 200 = 5100 > 5000)
    with pytest.raises((TransactionLimitError, InvalidAmountError)):
        # The exception now requires arguments
        service.withdraw(101, 200.00)


@patch('src.BankService.DatabaseManager')
def test_withdraw_with_fee(mock_db, service):
    """Test withdrawal under $100 correctly applies $2.00 fee."""
    # Setup Mock: Start with $100 balance
    mock_db.fetch_one.side_effect = [
        # 1. Fetch for calculation (balance: 100.00)
        {
            'balance': 100.00,
            'daily_withdrawn_amount': 0.00,
            'last_withdrawal_date': date.today()
        },
        # 2. Fetch for final balance check (Expected: 100.00 - 50.00 - 2.00 = 48.00)
        {'balance': 48.00}
    ]

    # Act: Withdraw $50.00 (triggers $2 fee, total deduction $52.00)
    service.withdraw(101, 50.00)

    # Assert 1: Check the account update query
    # The first execute_query is the account update
    update_call_args = mock_db.execute_query.call_args_list[0]
    # Check total deduction should be 52.00 (50.00 + 2.00 fee)
    assert update_call_args[0][1] == Decimal('52.00')

    # Assert 2: Check transaction logging (2 transactions: WITHDRAWAL and FEE)
    # Note: call_args_list[1] is the WITHDRAWAL log, call_args_list[2] is the FEE log
    withdrawal_log_args = mock_db.execute_query.call_args_list[1][0]
    fee_log_args = mock_db.execute_query.call_args_list[2][0]

    assert withdrawal_log_args[1] == 'WITHDRAWAL'
    assert fee_log_args[1] == 'FEE'
    assert fee_log_args[2] == Decimal('2.00')


@patch('src.BankService.DatabaseManager')
def test_withdraw_no_fee(mock_db, service):
    """Test withdrawal over $100 correctly avoids the fee."""
    # Setup Mock: Start with $300 balance
    mock_db.fetch_one.side_effect = [
        {
            'balance': 300.00,
            'daily_withdrawn_amount': 0.00,
            'last_withdrawal_date': date.today()
        },
        {'balance': 100.00}
    ]

    # Act: Withdraw $200.00 (no fee, total deduction $200.00)
    service.withdraw(101, 200.00)

    # Assert 1: Check the account update query
    update_call_args = mock_db.execute_query.call_args_list[0][0]
    # total_deduction (index 0) should be 200.00
    assert update_call_args[1] == Decimal('200.00')

    # Assert 2: Check transaction logging (Only 1 transaction: WITHDRAWAL)
    assert mock_db.execute_query.call_count == 2
