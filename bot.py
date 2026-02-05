import os
from aiohttp import web
from typing import Callable, Awaitable, Dict, Any

from aiogram import Bot, Dispatcher, BaseMiddleware, types
from aiogram.types import Update
from aiogram.filters import Command
from aiogram.enums import ParseMode

# ───────── ENV VARIABLES ─────────

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing")

if not WEBHOOK_URL:
    raise RuntimeError("WEBHOOK_URL is missing")

SUDO_USERS = set(
    int(x) for x in os.getenv("SUDO_USERS", "").split(",") if x
)

print("Loaded SUDO_USERS:", SUDO_USERS)

# ───────── BOT SETUP ─────────

bot = Bot(
    token=BOT_TOKEN,
    parse_mode=ParseMode.HTML,
    request_timeout=60
)

dp = Dispatcher()


# ───────── AUTH MIDDLEWARE (FIX) ─────────

class SudoMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[types.Message, Dict[str, Any]], Awaitable[Any]],
        event: types.Message,
        data: Dict[str, Any],
    ):
        if event.from_user.id not in SUDO_USERS:
            await event.answer("🚫 Unauthorized")
            return
        return await handler(event, data)


dp.message.middleware(SudoMiddleware())


# ───────── COMMANDS ─────────

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer("✅ Bot is running and authorized.")


@dp.message(Command("ping"))
async def ping_cmd(message: types.Message):
    await message.answer("🏓 Pong!")


# ───────── WEBHOOK HANDLER ─────────

async def handle_webhook(request: web.Request):
    data = await request.json()
    update = Update.model_validate(data)
    await dp.feed_update(bot, update)
    return web.Response(text="OK")


# ───────── APP LIFECYCLE ─────────

async def on_startup(app: web.Application):
    print("Setting webhook...")
    await bot.set_webhook(
        WEBHOOK_URL,
        drop_pending_updates=True
    )
    print("Webhook set successfully")


async def on_shutdown(app: web.Application):
    print("Shutting down...")
    await bot.delete_webhook()
    await bot.session.close()


async def create_app():
    app = web.Application()
    app.router.add_post("/webhook", handle_webhook)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    return app


# ───────── RUN ─────────

if __name__ == "__main__":
    web.run_app(create_app(), port=8000)
