# =========================================================
# src/DatabaseManager.py
# Defines the public interface for the 'src' package
# =========================================================

import os
import sys
import time
import mysql.connector
from mysql.connector import Error

# Configuration is moved to main.py or service.py to keep the DB layer clean,
# but we'll include a placeholder config here for simplicity if running DB stand-alone.
# In a true system, this would be passed in via dependency injection.
DB_CONFIG = {
    # Defaults to localhost if not set
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'password'),
    'database': os.getenv('DB_NAME', 'atm_db')
}


class DatabaseManager:
    """
    Handles raw database interactions (Connection, Cursor, Commit/Rollback).
    It ensures connections are opened and safely closed.
    """
    @staticmethod
    def get_connection():
        """
        Includes a retry mechanism. 
        Docker containers start simultaneously, but MySQL takes seconds to boot.
        This loop prevents the Python app from crashing immediately.
        """
        retries = 5
        while retries > 0:
            try:
                connection = mysql.connector.connect(**DB_CONFIG)
                if connection.is_connected():
                    return connection
            except Error as e:
                # If authenticating failed, don't retry, just fail.
                if e.errno == 1045:
                    print("Authentication failed. Check passwords.")
                    sys.exit(1)

                # If connection failed (DB not ready), wait and retry
                print(f"Database not ready yet... retrying ({retries} left)")
                time.sleep(5)
                retries -= 1

        print("Could not connect to database after multiple attempts.")
        sys.exit(1)

    @staticmethod
    def execute_query(query, *args):
        """Executes an INSERT/UPDATE/DELETE query and commits the transaction."""
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, args if args else ())
            conn.commit()
            return cursor.lastrowid
        except Error as e:
            conn.rollback()  # Ensure data integrity on failure
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def fetch_one(query, params=None):
        """Fetches a single row, returns it as a dictionary."""
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(query, params or ())
            return cursor.fetchone()
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def fetch_all(query, params=None):
        """Fetches all rows, returns them as a list of dictionaries."""
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(query, params or ())
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()
