import os
from telegram import Bot

from collections import defaultdict

import logging

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

to_introduce = {}
violations = {}
seen_users = defaultdict(dict)
user_info = defaultdict(dict)

bot = Bot(os.environ.get('BOT_TOKEN'))
