from pathlib import Path

files = {
    'config/settings.py': Path('config/settings.py'),
    '.env': Path('.env'),
    'handlers/messages.py': Path('handlers/messages.py'),
}

replacements = [
    # config/settings.py patches
    (
        'config/settings.py',
        'BOT_TOKEN = os.getenv("BOT_TOKEN")\nADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()]\n\nif not BOT_TOKEN:\n    raise ValueError("សូមពិនិត្យមើល! អ្នកមិនទាន់បានដាក់ BOT_TOKEN នៅក្នុង .env ទេ ឬរកវាលែងឃើញ។")',
        'BOT_TOKEN = os.getenv("BOT_TOKEN")\nDATABASE_URL = os.getenv("DATABASE_URL")\nADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()]\n\nif not BOT_TOKEN:\n    raise ValueError("សូមពិនិត្យមើល! អ្នកមិនទាន់បានដាក់ BOT_TOKEN នៅក្នុង .env ទេ ឬរកវាលែងឃើញ។")\nif not DATABASE_URL:\n    raise ValueError("សូមពិនិត្យមើល! អ្នកមិនទាន់បានដាក់ DATABASE_URL នៅក្នុង .env ទេ ឬរកវាលែងឃើញ។")'
    ),
    (
        'config/settings.py',
        'load_dotenv()\n\nBOT_TOKEN = os.getenv("BOT_TOKEN")',
        'load_dotenv()\n\nBOT_TOKEN = os.getenv("BOT_TOKEN")\nDATABASE_URL = os.getenv("DATABASE_URL")'
    ),
    (
        'config/settings.py',
        'from dotenv import load_dotenv\n',
        'from dotenv import load_dotenv\nimport psycopg2\n'
    ),
    (
        'config/settings.py',
        'if not DATABASE_URL:\n    raise ValueError("សូមពិនិត្យមើល! អ្នកមិនទាន់បានដាក់ DATABASE_URL នៅក្នុង .env ទេ ឬរកវាលែងឃើញ។")',
        'if not DATABASE_URL:\n    raise ValueError("សូមពិនិត្យមើល! អ្នកមិនទាន់បានដាក់ DATABASE_URL នៅក្នុង .env ទេ ឬរកវាលែងឃើញ។")\n\n\ndef get_db_connection():\n    return psycopg2.connect(DATABASE_URL, sslmode="require")'
    ),
    # .env patch
    (
        '.env',
        'DATABASE_URL=postgresql://postgres:barangpgb@2026@db.fwvnrkxifrsxgrrfhrgd.supabase.co:5432/postgres',
        'DATABASE_URL=postgresql://postgres:barangpgb%402026@db.fwvnrkxifrsxgrrfhrgd.supabase.co:5432/postgres'
    ),
    # handlers/messages.py patches
    (
        'handlers/messages.py',
        'import re\nimport sqlite3\nfrom telegram import Update, ReplyKeyboardMarkup\nfrom telegram.ext import ContextTypes\nfrom config import settings as SETTINGS\n',
        'import re\nfrom telegram import Update, ReplyKeyboardMarkup\nfrom telegram.ext import ContextTypes\nfrom config import settings as SETTINGS\n'
    ),
    (
        'handlers/messages.py',
        'conn = sqlite3.connect("delivery_bot.db")\n        cursor = conn.cursor()',
        'conn = SETTINGS.get_db_connection()\n        cursor = conn.cursor()'
    ),
    (
        'handlers/messages.py',
        'cursor.execute(\n            "SELECT dispatch_id, driver_id, item_details, customer_phone, customer_id FROM dispatches WHERE customer_id = ? ORDER BY dispatch_id DESC LIMIT 1", \n            (user_id,)\n        )',
        'cursor.execute(\n            "SELECT dispatch_id, driver_id, item_details, customer_phone, customer_id FROM dispatches WHERE customer_id = %s ORDER BY dispatch_id DESC LIMIT 1", \n            (user_id,)\n        )'
    ),
    (
        'handlers/messages.py',
        'cursor.execute("UPDATE dispatches SET customer_location = ? WHERE dispatch_id = ?", (google_map_url, dispatch_id))',
        'cursor.execute("UPDATE dispatches SET customer_location = %s WHERE dispatch_id = %s", (google_map_url, dispatch_id))'
    ),
    (
        'handlers/messages.py',
        'cursor.execute("UPDATE users SET phone = ? WHERE user_id = ?", (phone_number, contact_user_id))',
        'cursor.execute("UPDATE users SET phone = %s WHERE user_id = %s", (phone_number, contact_user_id))'
    ),
    (
        'handlers/messages.py',
        'conn = sqlite3.connect("delivery_bot.db")\n        cursor = conn.cursor()\n        cursor.execute("SELECT item_details, status, dispatch_date FROM dispatches WHERE customer_id = ? ORDER BY dispatch_id DESC LIMIT 1", (user_id,))\n        active_delivery = cursor.fetchone()\n        conn.close()',
        'conn = SETTINGS.get_db_connection()\n        cursor = conn.cursor()\n        cursor.execute("SELECT item_details, status, dispatch_date FROM dispatches WHERE customer_id = %s ORDER BY dispatch_id DESC LIMIT 1", (user_id,))\n        active_delivery = cursor.fetchone()\n        cursor.close()\n        conn.close()'
    ),
    (
        'handlers/messages.py',
        'conn = sqlite3.connect("delivery_bot.db")\n        cursor = conn.cursor()',
        'conn = SETTINGS.get_db_connection()\n        cursor = conn.cursor()'
    ),
    (
        'handlers/messages.py',
        'cursor.execute(\n            "SELECT user_id, first_name FROM users WHERE phone IN (?, ?, ?)", \n            (phone_variant1, phone_variant2, phone_variant3)\n        )',
        'cursor.execute(\n            "SELECT user_id, first_name FROM users WHERE phone IN (%s, %s, %s)", \n            (phone_variant1, phone_variant2, phone_variant3)\n        )'
    ),
    (
        'handlers/messages.py',
        'cursor.execute(\n                "INSERT INTO dispatches (driver_id, customer_phone, customer_id, item_details) VALUES (?, ?, ?, ?)",\n                (user_id, customer_phone, cust_id, item_details)\n            )',
        'cursor.execute(\n                "INSERT INTO dispatches (driver_id, customer_phone, customer_id, item_details) VALUES (%s, %s, %s, %s)",\n                (user_id, customer_phone, cust_id, item_details)\n            )'
    ),
    (
        'handlers/messages.py',
        'cursor.execute(\n                "INSERT INTO dispatches (driver_id, customer_phone, item_details) VALUES (?, ?, ?)",\n                (user_id, customer_phone, item_details)\n            )\n            conn.commit()\n            \n            dispatch_id = cursor.lastrowid',
        'cursor.execute(\n                "INSERT INTO dispatches (driver_id, customer_phone, item_details) VALUES (%s, %s, %s) RETURNING dispatch_id",\n                (user_id, customer_phone, item_details)\n            )\n            dispatch_id = cursor.fetchone()[0]\n            conn.commit()'
    ),
]

for filename, old, new in replacements:
    path = files[filename]
    text = path.read_text(encoding='utf-8')
    if old not in text:
        print(f'MISSING in {filename}: {old[:80]}...')
        continue
    path.write_text(text.replace(old, new), encoding='utf-8')

print('Patch complete')
