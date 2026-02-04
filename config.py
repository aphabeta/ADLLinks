import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "telegram_bot"

FORCE_JOIN_CHANNEL = os.getenv("FORCE_JOIN_CHANNEL")  # @channelusername
