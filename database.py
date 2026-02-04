from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI, DB_NAME

client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]

categories = db.categories
buttons = db.buttons
sudo_users = db.sudo_users
force_channels = db.force_channels
clicks = db.clicks
