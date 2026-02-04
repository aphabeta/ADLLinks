from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def force_join_keyboard(channels):
    kb = []
    for ch in channels:
        kb.append([
            InlineKeyboardButton(
                text=f"📢 Join {ch['username']}",
                url=f"https://t.me/{ch['username'].lstrip('@')}"
            )
        ])
    kb.append([InlineKeyboardButton(text="✅ Check Again", callback_data="check_join")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def categories_keyboard(cats):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=c["name"], callback_data=f"cat:{c['_id']}")]
            for c in cats
        ]
    )

def buttons_keyboard(btns):
    kb = []
    for b in btns:
        kb.append([
            InlineKeyboardButton(
                text=b["text"],
                callback_data=f"click:{b['_id']}"
            )
        ])
    kb.append([InlineKeyboardButton(text="⬅ Back", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=kb)
