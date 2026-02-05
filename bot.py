from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiohttp import web
from bson import ObjectId
from datetime import datetime

from config import BOT_TOKEN, WEBHOOK_URL
from database import (
    categories, buttons, sudo_users,
    force_channels, clicks
)
from keyboards import (
    force_join_keyboard,
    categories_keyboard,
    buttons_keyboard
)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ---------- HELPERS ----------
async def is_sudo(user_id):
    return await sudo_users.find_one({"user_id": user_id})

async def missing_channels(user_id):
    required = await force_channels.find().to_list(50)
    missing = []

    for ch in required:
        try:
            member = await bot.get_chat_member(ch["username"], user_id)
            if member.status not in ("member", "administrator", "creator"):
                missing.append(ch)
        except:
            missing.append(ch)

    return missing

# ---------- START ----------
@dp.message(CommandStart())
async def start(message: types.Message):
    missing = await missing_channels(message.from_user.id)

    if missing:
        return await message.answer(
            "🚫 You must join all channels below:",
            reply_markup=force_join_keyboard(missing)
        )

    cats = await categories.find().to_list(100)
    if not cats:
        return await message.answer("No categories available yet.")

    await message.answer(
        "📂 Choose a category:",
        reply_markup=categories_keyboard(cats)
    )

# ---------- CALLBACKS ----------
@dp.callback_query()
async def callbacks(call: types.CallbackQuery):
    if call.data == "check_join":
        return await start(call.message)

    if call.data.startswith("cat:"):
        cat_id = call.data.split(":")[1]
        btns = await buttons.find({"category_id": cat_id}).to_list(100)

        if not btns:
            return await call.message.edit_text("No links here yet.")

        await call.message.edit_text(
            "🔗 Choose a link:",
            reply_markup=buttons_keyboard(btns)
        )

    if call.data.startswith("click:"):
        btn_id = call.data.split(":")[1]
        button = await buttons.find_one({"_id": ObjectId(btn_id)})

        if not button:
            return await call.answer("Invalid link", show_alert=True)

        # 🔢 Analytics
        await clicks.insert_one({
            "button_id": btn_id,
            "user_id": call.from_user.id,
            "timestamp": datetime.utcnow()
        })

        await call.answer("Opening link…")
        await call.message.answer(button["url"])

    if call.data == "back":
        cats = await categories.find().to_list(100)
        await call.message.edit_text(
            "📂 Choose a category:",
            reply_markup=categories_keyboard(cats)
        )

# ---------- ADMIN ----------
@dp.message(Command("addchannel"))
async def add_channel(message: types.Message):
    if not await is_sudo(message.from_user.id):
        return await message.answer("❌ Unauthorized")

    username = message.text.replace("/addchannel", "").strip()
    await force_channels.insert_one({"username": username})
    await message.answer(f"✅ Channel added: {username}")

@dp.message(Command("delchannel"))
async def del_channel(message: types.Message):
    if not await is_sudo(message.from_user.id):
        return await message.answer("❌ Unauthorized")

    username = message.text.replace("/delchannel", "").strip()
    await force_channels.delete_one({"username": username})
    await message.answer(f"🗑️ Channel removed: {username}")

@dp.message(Command("stats"))
async def stats(message: types.Message):
    if not await is_sudo(message.from_user.id):
        return await message.answer("❌ Unauthorized")

    pipeline = [
        {"$group": {"_id": "$button_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]

    data = await clicks.aggregate(pipeline).to_list(20)
    if not data:
        return await message.answer("No clicks yet.")

    text = "📊 Click Stats:\n\n"
    for d in data:
        btn = await buttons.find_one({"_id": ObjectId(d["_id"])})
        text += f"• {btn['text']} → {d['count']} clicks\n"

    await message.answer(text)

# ---------- WEBHOOK ----------
async def handle_webhook(request):
    update = types.Update(**await request.json())
    await dp.feed_update(bot, update)
    return web.Response(text="OK")

async def main():
    app = web.Application()
    app.router.add_post("/webhook", webhook_handler)

    async def on_startup(app):
        await bot.set_webhook(WEBHOOK_URL)

    async def on_shutdown(app):
        await bot.delete_webhook()

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    return app


if __name__ == "__main__":
    web.run_app(main(), port=8000)
