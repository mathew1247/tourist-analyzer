import os
import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash
from backend.config import Config

try:
    import mysql.connector
    from mysql.connector import Error as MySQLError
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False
    MySQLError = Exception

# Local SQLite fallback path if MySQL server is offline / not installed
SQLITE_DB_PATH = Path(__file__).resolve().parent / 'tourism_analytics.db'

# Tracks whether MySQL is actively reachable
_use_mysql = None


class DictCursorWrapper:
    """Provides dictionary-like row access for SQLite to match MySQL dictionary cursors."""
    def __init__(self, cursor):
        self.cursor = cursor

    def execute(self, query, params=None):
        # Convert MySQL %s placeholders to SQLite ? placeholders if using SQLite
        converted_query = query.replace('%s', '?')
        if params is not None:
            return self.cursor.execute(converted_query, params)
        return self.cursor.execute(converted_query)

    def executemany(self, query, seq_of_params):
        converted_query = query.replace('%s', '?')
        return self.cursor.executemany(converted_query, seq_of_params)

    def fetchone(self):
        row = self.cursor.fetchone()
        if row is None:
            return None
        return dict(row)

    def fetchall(self):
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]

    @property
    def lastrowid(self):
        return self.cursor.lastrowid

    @property
    def rowcount(self):
        return self.cursor.rowcount

    def close(self):
        self.cursor.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class DictConnectionWrapper:
    """Wraps an SQLite connection so it behaves identically to mysql.connector."""
    def __init__(self, conn):
        self.conn = conn

    def cursor(self, dictionary=True):
        raw_cursor = self.conn.cursor()
        return DictCursorWrapper(raw_cursor)

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()
        self.close()


def get_db_connection():
    """
    Establish and return a database connection.
    Prioritizes MySQL using credentials from Config.
    Falls back gracefully to SQLite if MySQL service is not reachable.
    """
    global _use_mysql

    if _use_mysql is not False and MYSQL_AVAILABLE:
        try:
            conn = mysql.connector.connect(
                host=Config.DB_HOST,
                port=Config.DB_PORT,
                database=Config.DB_NAME,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                connection_timeout=1
            )
            _use_mysql = True
            return conn
        except MySQLError as err:
            if _use_mysql is None:
                print(f"[Database] MySQL connection notice: {err}. Using local database fallback for immediate execution.")
            _use_mysql = False

    # SQLite fallback
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    return DictConnectionWrapper(conn)


def is_using_mysql():
    """Check if the backend is actively using MySQL."""
    global _use_mysql
    if _use_mysql is None:
        try:
            conn = get_db_connection()
            conn.close()
        except Exception:
            pass
    return bool(_use_mysql)


def init_db():
    """
    Initialize database tables and seed with initial categories, default admin,
    and 24 months of sample tourism data if not already present.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Create Tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTO_INCREMENT,
                username VARCHAR(100) NOT NULL,
                email VARCHAR(150) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL,
                role VARCHAR(50) DEFAULT 'admin',
                phone VARCHAR(50) DEFAULT '+91 98765 43210',
                company_name VARCHAR(150) DEFAULT 'XploreElite Tourism Analytics Ltd.',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP NULL
            );
        """ if is_using_mysql() else """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                role TEXT DEFAULT 'admin',
                phone TEXT DEFAULT '+91 98765 43210',
                company_name TEXT DEFAULT 'XploreElite Tourism Analytics Ltd.',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP NULL
            );
        """)

        # Graceful migration for existing databases without phone / company_name
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN phone TEXT DEFAULT '+91 98765 43210'")
        except Exception:
            pass
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN company_name TEXT DEFAULT 'XploreElite Tourism Analytics Ltd.'")
        except Exception:
            pass

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tourism_categories (
                id INTEGER PRIMARY KEY AUTO_INCREMENT,
                category_name VARCHAR(100) NOT NULL UNIQUE,
                avg_spend DECIMAL(10,2) DEFAULT 0.00,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """ if is_using_mysql() else """
            CREATE TABLE IF NOT EXISTS tourism_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_name TEXT NOT NULL UNIQUE,
                avg_spend REAL DEFAULT 0.00,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS monthly_analytics (
                id INTEGER PRIMARY KEY AUTO_INCREMENT,
                month VARCHAR(20) NOT NULL,
                year INT NOT NULL,
                visitors INT NOT NULL,
                revenue DECIMAL(12,2) NOT NULL,
                sii_index FLOAT NULL,
                category_id INT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES tourism_categories(id) ON DELETE SET NULL
            );
        """ if is_using_mysql() else """
            CREATE TABLE IF NOT EXISTS monthly_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                month TEXT NOT NULL,
                year INTEGER NOT NULL,
                visitors INTEGER NOT NULL,
                revenue REAL NOT NULL,
                sii_index REAL NULL,
                category_id INTEGER NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES tourism_categories(id) ON DELETE SET NULL
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_logs (
                id INTEGER PRIMARY KEY AUTO_INCREMENT,
                user_id INT NULL,
                username VARCHAR(100),
                last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                access_level VARCHAR(100)
            );
        """ if is_using_mysql() else """
            CREATE TABLE IF NOT EXISTS user_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NULL,
                username TEXT,
                last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                access_level TEXT
            );
        """)

        conn.commit()

        # Seed Categories if empty
        cursor.execute("SELECT COUNT(*) as count FROM tourism_categories")
        cat_count = cursor.fetchone()['count']
        if cat_count == 0:
            categories = [
                ('Beach Tourism', 3275.00),
                ('Hill Stations', 3900.00),
                ('Cultural & Heritage', 2800.00),
                ('Adventure', 4200.00),
                ('Others', 2500.00)
            ]
            for cat, spend in categories:
                cursor.execute(
                    "INSERT INTO tourism_categories (category_name, avg_spend) VALUES (%s, %s)",
                    (cat, spend)
                )
            conn.commit()

        # Seed Default Admins if empty
        cursor.execute("SELECT COUNT(*) as count FROM users")
        user_count = cursor.fetchone()['count']
        if user_count == 0:
            admin1_pwd = generate_password_hash('Admin@123')
            admin2_pwd = generate_password_hash('admin123')
            cursor.execute(
                "INSERT INTO users (username, email, password, role) VALUES (%s, %s, %s, %s)",
                ('Admin', 'admin@tourism.com', admin1_pwd, 'admin')
            )
            cursor.execute(
                "INSERT INTO users (username, email, password, role) VALUES (%s, %s, %s, %s)",
                ('Admin User', 'admin@xploreelite.com', admin2_pwd, 'admin')
            )
            conn.commit()

        # Seed Monthly Tourism Analytics (2025 + 2024 baseline) if empty
        cursor.execute("SELECT COUNT(*) as count FROM monthly_analytics")
        analytics_count = cursor.fetchone()['count']
        if analytics_count == 0:
            seed_data = [
                ('January', 2025, 3200, 520000.00, 0.85, 1),
                ('February', 2025, 3850, 615000.00, 0.92, 2),
                ('March', 2025, 4120, 680000.00, 1.05, 3),
                ('April', 2025, 5430, 890000.00, 1.25, 2),
                ('May', 2025, 4980, 810000.00, 1.40, 4),
                ('June', 2025, 4300, 710000.00, 1.15, 1),
                ('July', 2025, 3900, 640000.00, 0.98, 3),
                ('August', 2025, 3650, 600000.00, 0.90, 5),
                ('September', 2025, 3400, 560000.00, 0.88, 2),
                ('October', 2025, 4200, 690000.00, 1.08, 3),
                ('November', 2025, 4190, 670000.00, 1.06, 1),
                ('December', 2025, 5300, 850000.00, 1.30, 1),
                # 2024 records
                ('January', 2024, 2850, 450000.00, 0.80, 1),
                ('February', 2024, 3200, 510000.00, 0.88, 2),
                ('March', 2024, 3600, 570000.00, 0.95, 3),
                ('April', 2024, 4800, 760000.00, 1.15, 2),
                ('May', 2024, 4300, 690000.00, 1.20, 4),
                ('June', 2024, 3800, 600000.00, 1.02, 1),
                ('July', 2024, 3400, 540000.00, 0.90, 3),
                ('August', 2024, 3200, 510000.00, 0.85, 5),
                ('September', 2024, 3000, 480000.00, 0.82, 2),
                ('October', 2024, 3700, 590000.00, 0.98, 3),
                ('November', 2024, 3800, 600000.00, 1.00, 1),
                ('December', 2024, 4600, 720000.00, 1.20, 1)
            ]
            for row in seed_data:
                cursor.execute("""
                    INSERT INTO monthly_analytics (month, year, visitors, revenue, sii_index, category_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, row)
            conn.commit()

        print("[Database] Database initialized and verified successfully.")
    except Exception as err:
        conn.rollback()
        print(f"[Database Error] Could not initialize database: {err}")
        raise err
    finally:
        cursor.close()
        conn.close()
