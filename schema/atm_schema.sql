-- =========================================================
-- atm_schema.sql
-- Database Setup Script for ATM Management System
-- =========================================================

-- Drop existing database to start fresh
-- DROP DATABASE IF EXISTS atm_db;

-- Create the database if it doesn't exist
CREATE DATABASE IF NOT EXISTS atm_db;

-- Use the newly created database
USE atm_db;

-- Users table: Stores authentication details
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    pin_hash VARCHAR(64) NOT NULL, -- Storing SHA-256 hash, not plain text
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Accounts table: Stores financial data and limit tracking
CREATE TABLE IF NOT EXISTS accounts (
    account_number BIGINT PRIMARY KEY, -- 12-digit account number
    user_id INT,
    balance DECIMAL(15, 2) DEFAULT 0.00,
    daily_withdrawn_amount DECIMAL(15, 2) DEFAULT 0.00,
    last_withdrawal_date DATE,
    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
);

-- Transactions table: Audit trail
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    account_id BIGINT,
    transaction_type ENUM(
        'DEPOSIT',
        'WITHDRAWAL',
        'TRANSFER',
        'FEE'
    ) NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    target_account_id BIGINT NULL, -- Only used for transfers
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES accounts (account_number)
);

-- Logs table: System logs for monitoring and debugging
CREATE TABLE IF NOT EXISTS logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    log_level ENUM('INFO', 'WARNING', 'ERROR') NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- OPTIONAL: Add an index for faster lookup on open transactions
CREATE INDEX idx_open_transactions ON transactions (
    account_id,
    transaction_type,
    timestamp
);