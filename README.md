# 🏧 ATM Management System (AMS)

## ATM Management System (Python | MySQL | Docker | Pytest)

## 🌟 Project Overview

This project is a high-fidelity, production-style simulation of a backend **ATM Management System**. It demonstrates robust **Object-Oriented Programming (OOP)** design, secure data handling, complex business rule enforcement (like daily withdrawal limits), and modern DevOps practices (Docker).

Designed as a portfolio piece, it separates concerns strictly between the Presentation Layer (CLI), the Business Logic Layer, and the Data Access Layer.

## 🚀 Technology Stack

| Component            | Technology               | Role                                                                           |
| :------------------- | :----------------------- | :----------------------------------------------------------------------------- |
| **Language**         | Python 3.11+              | Core application logic and OOP structure.                                      |
| **Database**         | MySQL 8.0                | Secure, persistent data storage for ACID properties.                           |
| **Containerization** | Docker & Docker Compose  | Creates a portable, self-contained development environment.                    |
| **Testing**          | Pytest & `unittest.mock` | Unit testing to ensure business rules (e.g., limits, transactions) are robust. |
| **Security**         | `hashlib` (SHA-256)      | Used for secure, one-way hashing of user PINs.                                 |
| **Precision**        | `decimal` module         | Used for all monetary calculations to prevent floating-point errors.           |

## 🏗️ Architecture Design

The system follows a strict 3-Layer Architecture pattern:

1. **Presentation Layer (`ATM` class):** Handles user input/output (CLI).
2. **Business Logic Layer (`BankService` class):** The "brain." Enforces limits, executes transfers, and handles authentication.
3. **Data Access Layer (`DatabaseManager` class):** Isolates raw SQL queries and manages the MySQL connection lifecycle securely.

## ⚙️ Features Implemented

The system enforces several real-world banking constraints:

| Feature              | Constraint / Implementation Detail                                                                                               |
| :------------------- | :------------------------------------------------------------------------------------------------------------------------------- |
| **Authentication**   | Secure login using SHA-256 PIN hashing.                                                                                          |
| **Account Creation** | Links a User (authentication) to an Account (financial data).                                                                    |
| **Withdrawal**       | Enforces a per-transaction limit and a **daily cumulative withdrawal limit** ($5000.00), which resets based on the current date. |
| **Transactions**     | Supports Deposit, Withdrawal, and Transfers between accounts.                                                                    |
| **Error Handling**   | Uses custom exceptions (`InsufficientFundsError`, `TransactionLimitError`) for clean signaling between layers.                   |
| **Database**         | Uses parameterized queries via `mysql-connector` to prevent SQL Injection.                                                       |

## 🛠️ Setup and Running the Project

The entire system is containerized for easy setup.

### Prerequisites

1. [Docker](https://www.docker.com/get-started) must be installed and running on your machine.
2. Python 3 (to run tests outside of Docker).

### Step 1: Clone the Repository

```bash
git clone [YOUR_REPO_URL] atm-management-system
cd atm-management-system
```

### Step 2: Build and Run Services with Docker Compose

This command builds the Python application image and starts both the app and db services.

```bash
docker-compose up --build -d
```

### Step 3: Access the ATM CLI

Attach to the running application container to start interacting with the command-line interface:

```bash
docker attach atm_app_container
```

(Use Ctrl+C to detach without stopping the container)

### Step 4: Stop the Services

```bash
docker-compose down
```

## ✅ Running Unit Tests

The tests/test_atm.py file contains comprehensive unit tests that utilize Python's unittest.mock to simulate database responses. This ensures the business logic is verified without depending on the live MySQL container.

### Running Tests

```bash
pip install -r requirements.txt
pytest -v tests/
```

- Key Tests Demonstrated
  - Limit Reset Logic: Verifies the daily withdrawal counter resets correctly when the system date changes.
  - Security Check: Ensures PINs are hashed before comparison.
  - Edge Cases: Confirms exceptions like `InsufficientFundsError` and `TransactionLimitError` are raised correctly.

## 📜 Database Schema (config/setup.sql)

The schema design ensures data integrity and supports the daily withdrawal tracking requirement.

```sql
-- accounts table tracks daily withdrawal amount and date for limit enforcement.
CREATE TABLE accounts (
    account_number INT AUTO_INCREMENT PRIMARY KEY,
    -- ... other fields ...
    daily_withdrawn_amount DECIMAL(15, 2),
    last_withdrawal_date DATE
);

-- transactions table provides a complete audit trail.
CREATE TABLE transactions (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    -- ... other fields ...
    transaction_type ENUM('DEPOSIT', 'WITHDRAWAL', 'TRANSFER') NOT NULL,
    amount DECIMAL(15, 2)
);
```
