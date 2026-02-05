import os
import json
from aiohttp import web

from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import CommandStart
from aiogram.types import Update

# ================= CONFIG =================

BOT_TOKEN = os.getenv("BOT_TOKEN")

SUDO_USERS = set(
    int(x) for x in os.getenv("SUDO_USERS", "").split(",") if x.strip()
)

WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = os.getenv("WEBHOOK_URL") + WEBHOOK_PATH

# ================= BOT SETUP =================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

# ================= HELPERS =================

def is_sudo(user_id: int) -> bool:
    return user_id in SUDO_USERS

# ================= HANDLERS =================

@router.message(CommandStart())
async def start_cmd(message: types.Message):
    if not is_sudo(message.from_user.id):
        await message.answer("🚫 Unauthorized")
        return

    await message.answer("✅ Bot is working and you are authorized.")

# ================= WEBHOOK =================

async def handle_webhook(request: web.Request):
    try:
        data = await request.json()
        update = Update.model_validate(data)
        await dp.feed_update(bot, update)
        return web.Response(text="OK")
    except Exception as e:
        print("Webhook error:", e)
        return web.Response(status=500, text="ERROR")

# ================= APP =================

async def on_startup(app: web.Application):
    await bot.set_webhook(WEBHOOK_URL)
    print("Webhook set:", WEBHOOK_URL)

async def on_shutdown(app: web.Application):
    await bot.delete_webhook()
    await bot.session.close()

app = web.Application()
app.router.add_post(WEBHOOK_PATH, handle_webhook)
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

# ================= RUN =================

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
