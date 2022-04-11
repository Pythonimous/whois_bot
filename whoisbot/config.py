import logging
import os

from pymongo import MongoClient
from telegram import Bot

token = os.environ.get('BOT_TOKEN')

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token)

client = MongoClient("mongodb://localhost:27017/")

base = client.get_database("gatekeeper_bot")

chats = base["chats"]
users = base["users"]
