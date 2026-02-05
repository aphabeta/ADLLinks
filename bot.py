import os
from aiohttp import web

from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import CommandStart
from aiogram.types import Update

# ================= CONFIG =================

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
SUDO_USERS = {
    int(x) for x in os.getenv("SUDO_USERS", "").split(",") if x.strip()
}

if not BOT_TOKEN or not WEBHOOK_URL:
    raise RuntimeError("Missing BOT_TOKEN or WEBHOOK_URL")

# ================= BOT =================

bot = Bot(BOT_TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

# ================= HANDLERS =================

@router.message(CommandStart())
async def start_cmd(message: types.Message):
    if message.from_user.id not in SUDO_USERS:
        await message.answer("🚫 Unauthorized")
        return

    await message.answer("✅ Bot is working. You are authorized.")

# ================= WEBHOOK =================

async def webhook_handler(request: web.Request):
    update = Update.model_validate(await request.json())
    await dp.feed_update(bot, update)
    return web.Response(text="OK")

# ================= APP =================

async def on_startup(app: web.Application):
    await bot.set_webhook(WEBHOOK_URL)
    print("Webhook set")

async def on_shutdown(app: web.Application):
    await bot.delete_webhook()
    await bot.session.close()

app = web.Application()
app.router.add_post("/webhook", webhook_handler)
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

if __name__ == "__main__":
    web.run_app(app, port=8000)
