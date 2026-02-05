import os
from aiohttp import web

from aiogram import Bot, Dispatcher, types
from aiogram.types import Update
from aiogram.filters import Command
from aiogram.enums import ParseMode

# ───────── ENV ─────────

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not BOT_TOKEN or not WEBHOOK_URL:
    raise RuntimeError("BOT_TOKEN or WEBHOOK_URL missing")

SUDO_USERS = set(
    int(x) for x in os.getenv("SUDO_USERS", "").split(",") if x
)

print("Loaded SUDO_USERS:", SUDO_USERS)

# ───────── BOT ─────────

bot = Bot(
    token=BOT_TOKEN,
    parse_mode=ParseMode.HTML,
    request_timeout=60  # prevents Telegram timeout issues
)
dp = Dispatcher()


# ───────── AUTH ─────────

from functools import wraps

def sudo_only(handler):
    @wraps(handler)
    async def wrapper(message: types.Message, **kwargs):
        if message.from_user.id not in SUDO_USERS:
            await message.answer("🚫 Unauthorized")
            return
        return await handler(message, **kwargs)
    return wrapper


# ───────── COMMANDS ─────────

@dp.message(Command("start"))
@sudo_only
async def start(message: types.Message):
    await message.answer("✅ Bot is live and authorized.")


# ───────── WEBHOOK ─────────

async def webhook_handler(request: web.Request):
    data = await request.json()
    update = Update.model_validate(data)
    await dp.feed_update(bot, update)
    return web.Response(text="OK")


# ───────── APP ─────────

async def on_startup(app: web.Application):
    print("Setting webhook…")
    await bot.set_webhook(
        WEBHOOK_URL,
        drop_pending_updates=True
    )
    print("Webhook set")


async def on_shutdown(app: web.Application):
    await bot.delete_webhook()
    await bot.session.close()


async def create_app():
    app = web.Application()
    app.router.add_post("/webhook", webhook_handler)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    return app


# ───────── RUN ─────────

if __name__ == "__main__":
    web.run_app(create_app(), port=8000)
