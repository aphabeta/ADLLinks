
# 🤖 Advanced Telegram Link Bot  
Multi-Channel Force Join • Categories • Analytics • MongoDB • Koyeb-Ready

A powerful, fully self-managed Telegram bot that displays link buttons organized into categories, enforces multi-channel force join, and tracks click analytics, all while running entirely on free tiers.

---

## ✨ Features

### 👤 User Features
- /start command with customizable welcome message
- Forced joining of multiple Telegram channels
- Category-based navigation (menus)
- Buttons that open links
- Clean inline keyboard UI

### 👑 Admin (Sudo) Features
- Add / remove force-join channels
- Add / remove categories
- Add buttons inside categories
- View click analytics
- MongoDB-based persistence (no data loss on restart)

### 📊 Analytics
- Tracks every button click
- Per-button click counts
- Timestamped records
- Viewable via admin command

### ☁️ Hosting
- Designed for Koyeb free tier
- Uses webhooks (no polling)
- Compatible with MongoDB Atlas free (M0)

---

## 🗂️ Project Structure

telegram-advanced-link-bot/
│
├── bot.py              # Main bot logic
├── config.py           # Environment config
├── database.py         # MongoDB connection
├── keyboards.py        # Inline keyboard layouts
├── requirements.txt    # Python dependencies
├── Dockerfile          # Koyeb deployment
└── README.md

---

## 🧰 Tech Stack

- Python 3.11
- aiogram 3.x
- aiohttp
- MongoDB Atlas (Motor async driver)
- Koyeb (Docker)

---

## 🔑 Prerequisites

### Telegram Bot
Create a bot using @BotFather and copy the BOT_TOKEN.

### MongoDB Atlas (Free)
- Create an account at https://www.mongodb.com/atlas
- Create an M0 (Free Tier) cluster
- Create a database user
- Whitelist IP: 0.0.0.0/0
- Copy MongoDB connection URI

### Koyeb
Create an account at https://www.koyeb.com

---

## ⚙️ Environment Variables

Set these in Koyeb → App → Environment Variables:

BOT_TOKEN=your_telegram_bot_token  
WEBHOOK_URL=https://your-app-name.koyeb.app/webhook  
MONGO_URI=mongodb+srv://user:password@cluster.mongodb.net/

---

## 🐳 Deploying on Koyeb

1. Push this repository to GitHub
2. Create a new Koyeb App
3. Choose GitHub as source
4. Select Docker deployment
5. Set port to 8000
6. Add environment variables
7. Deploy

---

## 👮 Sudo (Admin) Setup

Admins are stored in MongoDB.

Insert your Telegram user ID manually into the sudo_users collection:

{
  "user_id": 123456789
}

Use @userinfobot to get your Telegram ID.

---

## 📜 Commands

### User
/start – Start the bot

### Admin
/addchannel @channel  
/delchannel @channel  
/addcategory name  
/addbutton | category_id | button_name | https://link  
/stats

---

## ✏️ Customizing the Start Message

Open bot.py and locate:

@dp.message(CommandStart())

Change the message text inside:

await message.answer("Your custom message", reply_markup=...)

You can use emojis, Markdown, and multi-line text.

---

## 🛡️ Free Tier Safety

- Webhook-based (no polling)
- MongoDB Atlas free tier
- No background jobs
- No filesystem writes
- Async & lightweight

---

## 🚀 Optional Enhancements

- Inline admin panel
- CSV export of analytics
- Button ordering
- Multi-language support

---

## ✅ Status

Production-ready, scalable, restart-safe, and 100% free-tier compatible.
