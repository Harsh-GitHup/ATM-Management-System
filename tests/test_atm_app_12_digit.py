# =========================================================
# tests/test_atm_app.py
# Defines the Unit Tests for ACCOUNT CREATION TESTS (12-digit account number)
# =========================================================

import pytest
from unittest.mock import patch
from src.BankService import BankService


# -- TEST FIXTURES --
@pytest.fixture
def service():
    """Returns a fresh instance of BankService for each test."""
    return BankService()


# -- UNIT TESTS --
@patch('src.BankService.DatabaseManager')
def test_create_account_generates_12_digit_number(mock_db, service):
    """Test that create_account generates a 12-digit account number."""
    # Mock: No existing account with the generated number
    mock_db.fetch_one.return_value = None
    mock_db.execute_query.return_value = 1  # user_id

    account_number = service.create_account("John Doe", "1234")

    # Assert: Account number is 12 digits
    assert len(str(account_number)) == 12
    assert 100000000000 <= account_number <= 999999999999


@patch('src.BankService.DatabaseManager')
def test_create_account_inserts_user_and_account(mock_db, service):
    """Test that create_account creates both user and account records."""
    mock_db.fetch_one.return_value = None
    mock_db.execute_query.return_value = 1

    service.create_account("Jane Doe", "5678")

    # Assert: Two INSERT queries were executed (user + account)
    assert mock_db.execute_query.call_count == 2

    # First call: INSERT INTO users
    user_insert_call = mock_db.execute_query.call_args_list[0][0]
    assert "INSERT INTO users" in user_insert_call[0]
    assert user_insert_call[1] == "Jane Doe"  # name

    # Second call: INSERT INTO accounts
    account_insert_call = mock_db.execute_query.call_args_list[1][0]
    assert "INSERT INTO accounts" in account_insert_call[0]


@patch('src.BankService.DatabaseManager')
def test_generate_account_number_retries_on_collision(mock_db, service):
    """Test that account number generation retries if number already exists."""
    # First check returns existing account, second returns None
    mock_db.fetch_one.side_effect = [
        {'account_number': 123456789012},  # First number exists
        None  # Second number is unique
    ]

    account_number = service._generate_account_number()

    # Assert: fetch_one was called twice (retry happened)
    assert mock_db.fetch_one.call_count == 2
    assert len(str(account_number)) == 12


@patch('src.BankService.DatabaseManager')
@patch('src.BankService.random.randint')
def test_generate_account_number_uses_random(mock_randint, mock_db, service):
    """Test that account number is generated using random."""
    mock_randint.return_value = 987654321098
    mock_db.fetch_one.return_value = None

    account_number = service._generate_account_number()

    assert account_number == 987654321098
    mock_randint.assert_called_with(100000000000, 999999999999)
