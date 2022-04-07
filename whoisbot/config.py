import os
from telegram import Bot

import logging

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

to_introduce = {}
violations = {}

bot = Bot(os.environ.get('BOT_TOKEN'))
