import os
import asyncio
from aiohttp import web

from aiogram import Bot, Dispatcher, types
from aiogram.types import Update
from aiogram.filters import Command
from aiogram.enums import ParseMode

# ────────────────── ENV VARIABLES ──────────────────

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")

if not WEBHOOK_URL:
    raise RuntimeError("WEBHOOK_URL is not set")

# Parse SUDO_USERS correctly (VERY IMPORTANT)
SUDO_USERS = set(
    int(x) for x in os.getenv("SUDO_USERS", "").split(",") if x
)

print("SUDO_USERS loaded:", SUDO_USERS)

# ────────────────── BOT SETUP ──────────────────

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()


# ────────────────── AUTH DECORATOR ──────────────────

def sudo_only(handler):
    async def wrapper(message: types.Message, *args, **kwargs):
        user_id = message.from_user.id
        print("Incoming user:", user_id)

        if user_id not in SUDO_USERS:
            await message.reply("🚫 Unauthorized")
            return
        return await handler(message, *args, **kwargs)

    return wrapper


# ────────────────── COMMANDS ──────────────────

@dp.message(Command("start"))
@sudo_only
async def start_cmd(message: types.Message):
    await message.reply("✅ Bot is running and you are authorized.")


@dp.message(Command("ping"))
@sudo_only
async def ping_cmd(message: types.Message):
    await message.reply("🏓 Pong!")


# ────────────────── WEBHOOK HANDLER ──────────────────

async def handle_webhook(request: web.Request):
    data = await request.json()
    update = Update.model_validate(data)
    await dp.feed_update(bot, update)
    return web.Response(text="OK")


# ────────────────── APP LIFECYCLE ──────────────────

async def on_startup(app: web.Application):
    print("Setting webhook...")
    await bot.set_webhook(WEBHOOK_URL)
    print("Webhook set successfully")


async def on_shutdown(app: web.Application):
    print("Deleting webhook...")
    await bot.delete_webhook()
    await bot.session.close()


async def create_app():
    app = web.Application()
    app.router.add_post("/webhook", handle_webhook)

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    return app


# ────────────────── MAIN ──────────────────

if __name__ == "__main__":
    web.run_app(create_app(), port=8000)
