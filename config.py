import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TELEGRAM_TOKEN')
DB_URL = os.getenv('DATABASE_URL')  # postgresql+asyncpg://user:pass@host/dbname