import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# Comma-separated Telegram user IDs
SUDO_USERS = list(map(int, os.getenv("SUDO_USERS", "").split(",")))
