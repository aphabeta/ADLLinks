import os
import re
from aiohttp import web
from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import Command
from aiogram.types import (
    Update, InlineKeyboardMarkup, InlineKeyboardButton,
)
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
BASE_WEBHOOK_URL = os.getenv("WEBHOOK_URL")
WEBHOOK_PATH = "/webhook"
MONGODB_URI = os.getenv("MONGODB_URI")

if not BOT_TOKEN or not BASE_WEBHOOK_URL or not MONGODB_URI:
    raise RuntimeError("Missing environment variables")

WEBHOOK_URL = BASE_WEBHOOK_URL + WEBHOOK_PATH

SUDO_USERS = {
    int(x) for x in os.getenv("SUDO_USERS", "").split(",") if x.strip()
}

# ================= BOT =================
from aiogram.client.default import DefaultBotProperties

bot = Bot(
    BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)

dp = Dispatcher()
router = Router()
dp.include_router(router)

# ================= DATABASE =================
mongo = AsyncIOMotorClient(MONGODB_URI)
db = mongo["adramalinks"]
users_col = db["users"]
categories_col = db["categories"]
buttons_col = db["buttons"]

# ================= STATE =================
PENDING_THUMBNAILS = {}  # admin_id -> drama name
PENDING_SETTHUMB = {}    # admin_id -> drama name

# ================= HELPERS =================
def is_admin(user_id: int) -> bool:
    return user_id in SUDO_USERS

async def unauthorized(message: types.Message):
    await message.answer("❌ Unauthorized")

async def register_user(message: types.Message):
    await users_col.update_one(
        {"user_id": message.from_user.id},
        {
            "$setOnInsert": {
                "user_id": message.from_user.id,
                "username": message.from_user.username,
                "first_name": message.from_user.first_name,
            }
        },
        upsert=True,
    )

# ================= KEYBOARDS =================
async def build_categories_kb():
    categories = await categories_col.find().to_list(None)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=c["name"], callback_data=f"cat:{c['name']}")]
            for c in categories
        ]
    )

async def build_dramas_kb(category: str):
    dramas = await buttons_col.find({"category": category}).to_list(None)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=d["text"], callback_data=f"drama:{d['text']}")]
            for d in dramas
        ]
    )

# ================= PUBLIC =================
@router.message(Command("start"))
async def start_cmd(message: types.Message):
    await register_user(message)
    await message.answer(
        "🎬 Welcome to ADrama Lovers Links Bot\n\n"
        "Click on a category below to see dramas.",
        reply_markup=await build_categories_kb(),
    )

@router.message(Command("find"))
async def find_cmd(message: types.Message):
    await register_user(message)
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        return await message.answer("Usage:\n/find <keyword>")
    keyword = args[1]
    dramas = await buttons_col.find(
        {"text": {"$regex": re.escape(keyword), "$options": "i"}}
    ).to_list(20)

    if not dramas:
        return await message.answer("❌ No dramas found.")

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=d["text"], callback_data=f"drama:{d['text']}")]
            for d in dramas
        ]
    )
    await message.answer(f"🔎 Search results for: `{keyword}`", reply_markup=kb)

# ================= CALLBACKS =================
@router.callback_query(lambda c: c.data.startswith("cat:"))
async def category_clicked(call: types.CallbackQuery):
    category = call.data.split(":", 1)[1]
    kb = await build_dramas_kb(category)
    if not kb.inline_keyboard:
        return await call.answer("No dramas yet.", show_alert=True)
    await call.message.edit_text(
        f"📂 {category}\nSelect a drama:", reply_markup=kb,
    )

@router.callback_query(lambda c: c.data.startswith("drama:"))
async def drama_clicked(call: types.CallbackQuery):
    drama = call.data.split(":", 1)[1]
    data = await buttons_col.find_one({"text": drama})

    if not data:
        return await call.answer("Drama not found.", show_alert=True)

    if "thumb_file_id" in data:
        await call.message.answer_photo(
            photo=data["thumb_file_id"],
            caption=f"🎥 {drama}\n\n🔗 {data['url']}",
        )
    else:
        await call.message.answer(f"🎥 {drama}\n\n🔗 {data['url']}")

# ================= ADMIN =================
@router.message(Command("addcategory"))
async def add_category_cmd(message: types.Message):
    if not is_admin(message.from_user.id):
        return await unauthorized(message)
    name = message.text.split(maxsplit=1)[1]
    await categories_col.insert_one({"name": name})
    await message.answer(f"✅ Category added: {name}")

@router.message(Command("editcategory"))
async def edit_category_cmd(message: types.Message):
    if not is_admin(message.from_user.id):
        return await unauthorized(message)
    _, old, new = message.text.split(maxsplit=2)
    await categories_col.update_one({"name": old}, {"$set": {"name": new}})
    await buttons_col.update_many({"category": old}, {"$set": {"category": new}})
    await message.answer(f"✏️ Category renamed:\n{old} → {new}")

@router.message(Command("addbutton"))
async def add_button_cmd(message: types.Message):
    if not is_admin(message.from_user.id):
        return await unauthorized(message)
    _, category, text, url = message.text.split(maxsplit=3)
    await buttons_col.insert_one({"category": category, "text": text, "url": url})
    PENDING_THUMBNAILS[message.from_user.id] = text
    await message.answer(
        f"✅ Drama added: {text}\nSend poster image now."
    )

@router.message(Command("editdrama"))
async def edit_drama_cmd(message: types.Message):
    if not is_admin(message.from_user.id):
        return await unauthorized(message)
    _, old, new = message.text.split(maxsplit=2)
    await buttons_col.update_one({"text": old}, {"$set": {"text": new}})
    await message.answer(f"✏️ Drama renamed:\n{old} → {new}")

@router.message(Command("editlink"))
async def edit_link_cmd(message: types.Message):
    if not is_admin(message.from_user.id):
        return await unauthorized(message)
    _, drama, link = message.text.split(maxsplit=2)
    await buttons_col.update_one({"text": drama}, {"$set": {"url": link}})
    await message.answer(f"🔗 Link updated for {drama}")

@router.message(Command("setthumb"))
async def set_thumb_cmd(message: types.Message):
    if not is_admin(message.from_user.id):
        return await unauthorized(message)
    drama = message.text.split(maxsplit=1)[1]
    PENDING_SETTHUMB[message.from_user.id] = drama
    await message.answer("📸 Send the new poster image.")

@router.message(Command("delbutton"))
async def del_button_cmd(message: types.Message):
    if not is_admin(message.from_user.id):
        return await unauthorized(message)
    text = message.text.split(maxsplit=1)[1]
    await buttons_col.delete_one({"text": text})
    await message.answer(f"🗑️ Drama deleted: {text}")

@router.message(Command("stats"))
async def stats_cmd(message: types.Message):
    if not is_admin(message.from_user.id):
        return await unauthorized(message)
    await message.answer(
        "📊 Bot Statistics\n\n"
        f"Users: {await users_col.count_documents({})}\n"
        f"Categories: {await categories_col.count_documents({})}\n"
        f"Dramas: {await buttons_col.count_documents({})}"
    )

# ================= PHOTO HANDLER =================
@router.message(lambda m: m.photo)
async def photo_handler(message: types.Message):
    uid = message.from_user.id
    file_id = message.photo[-1].file_id

    if uid in PENDING_THUMBNAILS:
        drama = PENDING_THUMBNAILS.pop(uid)
        await buttons_col.update_one(
            {"text": drama},
            {"$set": {"thumb_file_id": file_id}},
        )
        return await message.answer(f"📸 Thumbnail saved for {drama}")

    if uid in PENDING_SETTHUMB:
        drama = PENDING_SETTHUMB.pop(uid)
        await buttons_col.update_one(
            {"text": drama},
            {"$set": {"thumb_file_id": file_id}},
        )
        return await message.answer(f"📸 New thumbnail set for {drama}")

# ================= WEBHOOK SETUP WITH RETRY =================
async def set_webhook_with_retry(bot, webhook_url, retries=5, delay=2):
    for attempt in range(1, retries + 1):
        try:
            await bot.set_webhook(webhook_url, drop_pending_updates=True)
            print("✅ Webhook set successfully")
            return
        except Exception as e:
            print(f"⚠️ Webhook set failed (attempt {attempt}): {e}")
            if attempt == retries:
                print("❌ All webhook retries failed")
            else:
                await asyncio.sleep(delay * attempt)

async def handle_webhook(request: web.Request):
    update = Update.model_validate(await request.json())
    await dp.feed_update(bot, update)
    return web.Response(text="OK")

async def on_startup(app: web.Application):
    await set_webhook_with_retry(bot, WEBHOOK_URL)

async def on_shutdown(app: web.Application):
    await bot.delete_webhook()
    await bot.session.close()
    mongo.close()

app = web.Application()
app.router.add_post(WEBHOOK_PATH, handle_webhook)
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=8000)
