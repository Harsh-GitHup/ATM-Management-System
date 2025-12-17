# 🏧 ATM Management System (AMS)

## ATM Management System (Python | MySQL | Docker | Pytest)

## 🌟 Project Overview

This project is a production-style simulation of a backend **ATM Management System** demonstrating:

- Robust **Object-Oriented Programming (OOP)** with 3-layer architecture
- Secure authentication with SHA-256 PIN hashing
- Complex business rule enforcement (daily withdrawal limits, transaction fees)
- Modern DevOps practices with Docker containerization
- Comprehensive unit testing with pytest and mocking

Designed as a portfolio piece, it strictly separates concerns between the Presentation Layer (CLI), Business Logic Layer, and Data Access Layer.

## 🚀 Technology Stack

| Component            | Technology                   | Role                                                          |
| :------------------- | :--------------------------- | :------------------------------------------------------------ |
| **Language**         | Python 3.11+                 | Core application logic and OOP structure                      |
| **Database**         | MySQL 8.0                    | Secure, persistent data storage with ACID properties          |
| **DB Connector**     | **`mysql-connector-python`** | **Enables Python communication with MySQL**                   |
| **Containerization** | Docker & Docker Compose      | Portable, self-contained development environment              |
| **Testing**          | `Pytest` & `unittest.mock`   | Unit testing for business rules validation                    |
| **Security**         | `hashlib` (SHA-256)          | Secure, one-way hashing of user PINs                          |
| **Precision**        | `decimal` module             | Accurate monetary calculations (avoids floating-point errors) |

## 🏗️ Architecture Design

The system follows a strict **3-Layer Architecture** pattern:

┌─────────────────────────────────────────────────────────────┐
│ Presentation Layer (ATM class) │ ← User Interface (CLI)
│ - Handles user input/output │
│ - Input validation │
└──────────────┬──────────────────────────────────────────────┘
│              |
┌──────────────▼──────────────────────────────────────────────┐
│ Business Logic (BankService) │ ← The "Brain"
│ - Authentication & Authorization │
│ - Transaction rules & limits │
│ - PIN hashing │
└──────────────┬──────────────────────────────────────────────┘
│              |
┌──────────────▼──────────────────────────────────────────────┐
│ Data Access (DatabaseManager) │ ← Database Layer
│ - SQL query execution │
│ - Connection management │
│ - Transaction handling │
└─────────────────────────────────────────────────────────────┘

## ⚙️ Features Implemented

| Feature                      | Implementation Details                                                                                   |
| :--------------------------- | :------------------------------------------------------------------------------------------------------- |
| **Authentication**           | Secure login using SHA-256 PIN hashing (never stores plain-text PINs)                                    |
| **Account Creation**         | Atomically creates User (authentication) and Account (financial data)                                    |
| **Deposit**                  | Adds funds to account with transaction logging                                                           |
| **Withdrawal**               | Enforces daily limit ($5,000), applies $2 fee for withdrawals under $100                                 |
| **Transfer**                 | Secure fund transfers between accounts with validation                                                   |
| **Transaction History**      | Audit trail of last 5 transactions                                                                       |
| **Error Handling**           | Custom exceptions (`InsufficientFundsError`, `TransactionLimitError`, `InvalidAmountError`, `AuthError`) |
| **SQL Injection Prevention** | Parameterized queries via `mysql-connector-python`                                                       |
| **Daily Limit Reset**        | Automatically resets withdrawal counter at midnight                                                      |

## 📁 Project Structure

```bash
📁ATM_Management_System/
  ├── app.py # Application entry point
  ├── main.py # Legacy monolithic version (not used in production)
  ├── requirements.txt # Python dependencies
  ├── Dockerfile # Container configuration for Python app
  ├── docker-compose.yml # Multi-container orchestration
  ├── .env.example # Environment variable template
  ├── schema/
      └── atm_schema.sql # Database schema with tables and indexes
  ├── src/ # Main application package
      ├── __init__.py # Package exports
      ├── ATM.py # Presentation Layer (CLI interface)
      ├── BankService.py # Business Logic Layer
      ├── DatabaseManager.py # Data Access Layer
      └── ATM_Exceptions.py # Custom exception classes
  └── tests/ # Unit test suite
      ├── __init__.py
      ├── test_atm.py # Tests for legacy main.py
      └── test_atm_app.py # Tests for src package modules
```

## 🛠️ Setup and Running the Project

The entire system is containerized for easy setup.

### Prerequisites

1. **Docker Desktop** - [Download and install Docker](https://www.docker.com/get-started)
2. **Git** - For cloning the repository
3. **Python 3.x** - For running tests locally

### Step 1: Clone the Repository

```bash
git clone https://github.com/Harsh-GitHup/ATM_Management_System.git
cd ATM_Management_System
```

### Step 2: Configure Environment Variables

The project uses default credentials defined in docker-compose.yml.
Create a `.env` file based on the provided `.env.example` To customize:

```bash
# Copy the example file
cp .env.example .env

# Edit with your preferred values
# Note: Keep these matching with docker-compose.yml
```

### Step 3: Build and Run (Start) Services with Docker Compose

<!-- This command builds the Docker images and starts the containers for both the MySQL database and the Python application. -->

This command builds the Python application image, creates the MySQL database, and initializes the schema:

```bash
docker-compose up --build
```

**What happens:**

- MySQL container starts and creates the atm_db database
- Python app container builds with dependencies
- Schema is initialized automatically
- Application starts in interactive mode

### Step 4: Interact with the ATM

The application runs in interactive mode. You'll see:

```plaintext
=== WELCOME TO PYTHON BANK ATM ===

1. Login
2. Create New Account
3. Exit
Select option:
```

**Note**: If the container starts before you can interact, attach to it:

```bash
docker attach atm_app_container
```

To detach without stopping: Ctrl + P, then Ctrl + Q

### Step 5: Stop Services

To stop the services, run:

```bash
# Stop and remove containers
docker-compose down

# Stop and remove containers + volumes (deletes database data)
docker-compose down -v
```

## 🧪 Running Unit Tests

The project includes comprehensive unit tests using `pytest` with mocked database responses.

### Run Tests Locally

- To run tests locally (ensure you have Python 3.9+ and dependencies installed):

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests with verbose output
pytest -v tests/

# Run specific test file
pytest -v tests/test_atm_app.py

# Run with coverage report
pytest --cov=src tests/
```

### Run Tests in Docker

To run tests inside the Docker container:

```bash
# Run tests inside the container
docker-compose run --rm app pytest -v tests/
```

### Test Coverage

**Key test cases:**

- ✅ PIN hashing security
- ✅ Authentication (valid/invalid credentials)
- ✅ Deposit validation
- ✅ Withdrawal with insufficient funds
- ✅ Daily withdrawal limit enforcement
- ✅ Daily limit reset on new day
- ✅ Transaction fee application
- ✅ Transfer validation

## 📊 Database Schema

The database design ensures data integrity and supports audit trails:

```sql
-- Users: Authentication data
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    pin_hash VARCHAR(64) NOT NULL,  -- SHA-256 hash
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Accounts: Financial data with daily limit tracking
CREATE TABLE accounts (
    account_number INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    balance DECIMAL(15, 2) DEFAULT 0.00,
    daily_withdrawn_amount DECIMAL(15, 2) DEFAULT 0.00,  -- Tracks daily total
    last_withdrawal_date DATE,                            -- For reset logic
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Transactions: Complete audit trail
CREATE TABLE transactions (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    account_id INT,
    transaction_type ENUM('DEPOSIT', 'WITHDRAWAL', 'TRANSFER', 'FEE'),
    amount DECIMAL(15, 2) NOT NULL,
    target_account_id INT NULL,  -- For transfers
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES accounts(account_number)
);

-- Logs: System monitoring (optional)
CREATE TABLE logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    log_level ENUM('INFO', 'WARNING', 'ERROR'),
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🔒 Security Features

- Password Hashing: PINs are hashed using SHA-256 before storage
- SQL Injection Prevention: All queries use parameterized statements
- Environment Variables: Sensitive credentials stored in environment variables
- Input Validation: All user inputs are validated before processing
- Session Management: User session data is isolated per connection

## Future Improvements

### Planned Features

- [ ] Database transaction rollback for transfers
- [ ] Account lockout after failed login attempts
- [ ] Interest calculation on savings accounts
- [ ] Email notifications for transactions
- [ ] Admin dashboard for monitoring
- [ ] RESTful API layer

## 📚 Learning Outcomes

This project demonstrates proficiency in:

- **Software Architecture:** 3-layer design pattern
- **OOP Principles:** Encapsulation, separation of concerns
- **Database Design:** Normalization, foreign keys, indexes
- **Security:** Hashing, parameterized queries, input validation
- **DevOps:** Docker multi-container orchestration
- **Testing:** Unit tests, mocking, TDD practices
- **Error Handling:** Custom exceptions, graceful degradation

## 📄 License

This project is created for educational and portfolio purposes.

## 👤 Author

***Harsh Kesharwani***

- GitHub:
- LinkedIn:
- Portfolio:
