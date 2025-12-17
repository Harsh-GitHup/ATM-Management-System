# =========================================================
# app.py
# Main execution file for the ATM Management System
# =========================================================

from src.ATM import ATM
from dotenv import load_dotenv

# Load environment variables from .env file BEFORE importing other modules
load_dotenv()


if __name__ == "__main__":
    # Initialize and start the application
    app = ATM()
    app.start()
