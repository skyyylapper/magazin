import os
from dotenv import load_dotenv

load_dotenv()

MAIN_BOT_TOKEN = os.getenv("MAIN_BOT_TOKEN")
ADMIN_BOT_TOKEN = os.getenv("ADMIN_BOT_TOKEN")
SEND_API_KEY = os.getenv("SEND_API_KEY")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(',')))
MAIN_BOT_USERNAME = os.getenv("MAIN_BOT_USERNAME", "my_shop_bot")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "support")
MANUAL_WALLET_ADDRESS = os.getenv("MANUAL_WALLET_ADDRESS", "")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///shop.db")
CURRENCY_UPDATE_INTERVAL = int(os.getenv("CURRENCY_UPDATE_INTERVAL", 1800))
ANTISPAM_MAX_INVOICES = int(os.getenv("ANTISPAM_MAX_INVOICES", 3))
ANTISPAM_TIMEFRAME = int(os.getenv("ANTISPAM_TIMEFRAME", 600))
ANTISPAM_BLOCK_DURATION = int(os.getenv("ANTISPAM_BLOCK_DURATION", 3600))
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "ru")
