import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = "telegram_bot"

FORCE_JOIN_CHANNEL = os.getenv("FORCE_JOIN_CHANNEL")  # @channelusername
