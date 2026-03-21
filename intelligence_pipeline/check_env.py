import os
from dotenv import load_dotenv

# Load .env
load_dotenv(".env")

print("=== Current Telegram Report Settings ===")
print(f"TELEGRAM_REPORT_BOT_TOKEN: {os.getenv('TELEGRAM_REPORT_BOT_TOKEN')}")
print(f"TELEGRAM_REPORT_CHAT_ID: {os.getenv('TELEGRAM_REPORT_CHAT_ID')}")
