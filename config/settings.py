import os
import sqlite3
from dotenv import load_dotenv
import urllib.parse as urlparse
import pymysql

# ផ្ទុកទិន្នន័យពី .env ចូលទៅក្នុង System Environment
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()]
SQLITE_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "delivery_bot.db"))
DB_BACKEND = "mysql"

if not BOT_TOKEN:
    raise ValueError("សូមពិនិត្យមើល! អ្នកមិនទាន់បានដាក់ BOT_TOKEN នៅក្នុង .env ទេ ឬរកវាលែងឃើញ។")


def _is_sqlite_cursor(cursor):
    return isinstance(cursor, sqlite3.Cursor)


def execute_query(cursor, sql, params=None):
    if params is None:
        params = ()

    if _is_sqlite_cursor(cursor):
        sql = sql.replace("%s", "?")
    return cursor.execute(sql, params)


def get_last_insert_id(cursor):
    if _is_sqlite_cursor(cursor):
        return cursor.lastrowid
    # For MySQL and sqlite we can use cursor.lastrowid
    if DB_BACKEND == "mysql":
        return cursor.lastrowid
    # Fallback for Postgres-like behavior
    cursor.execute("SELECT lastval()")
    return cursor.fetchone()[0]


def get_db_connection():
    global DB_BACKEND

    if DATABASE_URL:
        parsed = urlparse.urlparse(DATABASE_URL)
        # MySQL URL (mysql://user:pass@host:port/db)
        if parsed.scheme and parsed.scheme.startswith("mysql"):
            try:
                conn = pymysql.connect(
                    host=parsed.hostname,
                    port=parsed.port or 3306,
                    user=parsed.username,
                    password=parsed.password,
                    database=parsed.path.lstrip('/'),
                )
                DB_BACKEND = "mysql"
                return conn
            except Exception as err:
                print(f"⚠️ MySQL connection failed, falling back to SQLite: {err}")
                DB_BACKEND = "sqlite"
        else:
            # Try Postgres only if a non-mysql URL is provided
            try:
                import psycopg2
                conn = psycopg2.connect(DATABASE_URL, sslmode="require")
                DB_BACKEND = "postgres"
                return conn
            except Exception as err:
                print(f"⚠️ Postgres connection failed, falling back to SQLite: {err}")
                DB_BACKEND = "sqlite"

    sqlite_dir = os.path.dirname(SQLITE_DB_PATH)
    os.makedirs(sqlite_dir, exist_ok=True)
    conn = sqlite3.connect(SQLITE_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    DB_BACKEND = "sqlite"
    return conn