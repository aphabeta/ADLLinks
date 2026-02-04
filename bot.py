import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web

from config import BOT_TOKEN, WEBHOOK_URL, SUDO_USERS
from storage import load_buttons, save_buttons

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ---------- HELPERS ----------
def is_sudo(user_id: int) -> bool:
    return user_id in SUDO_USERS

def build_keyboard():
    buttons = load_buttons()
    keyboard = []

    for b in buttons:
        keyboard.append(
            [InlineKeyboardButton(text=b["text"], url=b["url"])]
        )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# ---------- USER ----------
@dp.message(CommandStart())
async def start(message: types.Message):
    keyboard = build_keyboard()
    if not keyboard.inline_keyboard:
        await message.answer("No buttons configured yet.")
    else:
        await message.answer("Choose a link 👇", reply_markup=keyboard)

# ---------- ADMIN ----------
@dp.message(Command("addbutton"))
async def add_button(message: types.Message):
    if not is_sudo(message.from_user.id):
        return await message.answer("❌ You are not authorized.")

    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        return await message.answer(
            "Usage:\n/addbutton Button Name | https://link.com"
        )

    try:
        text, url = args[2].split("|")
        text = text.strip()
        url = url.strip()
    except:
        return await message.answer("Invalid format.")

    buttons = load_buttons()
    buttons.append({"text": text, "url": url})
    save_buttons(buttons)

    await message.answer(f"✅ Button added:\n{text} → {url}")

@dp.message(Command("delbutton"))
async def del_button(message: types.Message):
    if not is_sudo(message.from_user.id):
        return await message.answer("❌ You are not authorized.")

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        return await message.answer("Usage:\n/delbutton Button Name")

    name = args[1].strip()
    buttons = load_buttons()

    new_buttons = [b for b in buttons if b["text"] != name]

    if len(new_buttons) == len(buttons):
        return await message.answer("❌ Button not found.")

    save_buttons(new_buttons)
    await message.answer(f"🗑️ Button '{name}' removed.")

@dp.message(Command("listbuttons"))
async def list_buttons(message: types.Message):
    if not is_sudo(message.from_user.id):
        return await message.answer("❌ You are not authorized.")

    buttons = load_buttons()
    if not buttons:
        return await message.answer("No buttons found.")

    text = "📋 Buttons:\n\n"
    for b in buttons:
        text += f"• {b['text']} → {b['url']}\n"

    await message.answer(text)

# ---------- WEBHOOK ----------
async def handle_webhook(request):
    data = await request.json()
    update = types.Update(**data)
    await dp.feed_update(bot, update)
    return web.Response(text="OK")

async def main():
    await bot.set_webhook(WEBHOOK_URL)
    app = web.Application()
    app.router.add_post("/webhook", handle_webhook)
    return app

if __name__ == "__main__":
    web.run_app(main(), port=8000)
