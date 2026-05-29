import os
from dotenv import load_dotenv
import psycopg2

# ផ្ទុកទិន្នន័យពី .env ចូលទៅក្នុង System Environment
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()]

if not BOT_TOKEN:
    raise ValueError("សូមពិនិត្យមើល! អ្នកមិនទាន់បានដាក់ BOT_TOKEN នៅក្នុង .env ទេ ឬរកវាលែងឃើញ។")
if not DATABASE_URL:
    raise ValueError("សូមពិនិត្យមើល! អ្នកមិនទាន់បានដាក់ DATABASE_URL នៅក្នុង .env ទេ ឬរកវាលែងឃើញ។")


def get_db_connection():
    return psycopg2.connect(DATABASE_URL, sslmode="require")