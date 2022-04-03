#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""bot.py: A Telegram bot to gatekeep your serverr"""

__author__ = "Pythonimous"


from telegram.ext import Updater, MessageHandler, CommandHandler, Filters
from apscheduler.schedulers.background import BackgroundScheduler
from telegram import Bot
import logging
import json

import time
import os

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


class BotConfig:
    """Class representing a bot configuration"""

    def __init__(self, file_path):
        self.path = file_path
        with open(file_path, 'r') as f:
            self.config = json.load(f)
        self.token = os.environ.get('BOT_TOKEN')
        self.PORT = os.getenv('PORT', default=8443)
        self.admins = self.config["admins"]
        self.to_introduce = {}
        self.violations = {}
        logger.info('Loaded bot:\n"%s"' % (json.dumps(self.config, indent=4, separators=(',', ': '))))
        return


class GatekeeperBot:
    """
    A bot that requires people to introduce themselves using #whois first.
    The bot bans people for 24h after failure to do so 3 times.
    """

    def __init__(self, file_path):
        self.config = BotConfig(file_path)
        self.updater = Updater(self.config.token, use_context=True)
        self.bot = Bot(self.config.token)

        # Enable scheduling
        self.scheduler = BackgroundScheduler()

    def _warn_user(self, update):
        """ Warn user of their 1st / 2nd #whois violation """
        chat_id = update.message.chat.id
        user_id = update.message.from_user.id
        user_name = update.message.from_user.username or update.message.from_user.first_name
        self.bot.deleteMessage(update.message.chat.id, update.message.message_id)
        self.config.violations[chat_id][user_id] += 1
        if self.config.violations[chat_id].get(user_id, 0) == 1:
            return "Ошибочка вышла, @{}!".format(user_name)
        elif self.config.violations[chat_id].get(user_id, 0) == 2:
            return "Не испытывай моё терпение, @{}!".format(user_name)

    def _remove_user(self, chat_id, user_id):
        if chat_id in self.config.to_introduce:
            for user in self.config.to_introduce[chat_id]:
                if user['id'] == user_id:
                    self.config.to_introduce[chat_id].remove(user)
                    break
        if chat_id in self.config.violations:
            if user_id in self.config.violations[chat_id]:
                del self.config.violations[chat_id][user_id]

    def _gatekeep_callback(self, update, context):
        message_text = update.message.text or "a"
        message_id = update.message.message_id
        chat_id = update.message.chat.id
        user_id = update.message.from_user.id
        user_name = update.message.from_user.username or update.message.from_user.first_name
        """ Remove any non-#whois message from a new user / 24h ban user for 3 violations """
        logger.info("User %s (%s) said: %s" % (user_name,
                                               update.message.from_user.id, update.message.text))

        if chat_id in self.config.to_introduce:
            if any([user['id'] == user_id for user in self.config.to_introduce[chat_id]]) and user_id not in self.config.admins:
                if "#whois" in message_text and len(message_text.replace("#whois", "").strip()) > 13:
                    self._remove_user(chat_id, user_id)

                elif self.config.violations[chat_id].get(user_id, 0) < 2:
                    warning = self._warn_user(update)
                    if "#whois" not in message_text or len(message_text.split()) - 1 < 5:
                        self.bot.sendMessage(chat_id, warning + "\nСначала представься за 5+ слов с хештегом #whois.")
                else:
                    self._remove_user(chat_id, user_id)
                    self.bot.deleteMessage(chat_id, message_id)
                    self.bot.sendMessage(chat_id, "Я предупреждал, @{}!  Посиди-ка в бане сутки 😊".
                                                  format(user_name))
                    banned_until = time.time() + 60 * 60 * 24
                    self.bot.banChatMember(chat_id, user_id,
                                           until_date=banned_until)

    def _start(self, update, context):
        self.bot.sendMessage(update.message.chat.id, "Привет! Просто добавь меня в чат, и я сделаю всё сам.\n"
                                                     "ВАЖНО: НЕ ЗАБУДЬ сделать меня администратором 😉")

    def _help(self, update, context):
        self.bot.sendMessage(update.message.chat.id, "Я работаю просто.\n"
                                                     "Каждый, кто заходит в МОЙ чат, должен представиться с #whois "
                                                     "за 5 слов и более. У него три попытки. Не смог? Бан на сутки! 😊\n"
                                                     "ВАЖНО: НЕ ЗАБУДЬ сделать меня администратором 😉\n"
                                                     "Я живу здесь: https://github.com/Pythonimous/whois_bot")

    def _autoban_callback(self):
        current_time = time.time()
        for chat_id in self.config.to_introduce:
            for user in self.config.to_introduce[chat_id]:
                if current_time >= user['ban_at']:
                    self.bot.sendMessage(chat_id, f"Banned {user['name']} for a week (no #whois in 24 hours)")
                    banned_until = current_time + 60 * 60 * 24 * 7
                    self.bot.banChatMember(chat_id, user['id'],
                                           until_date=banned_until)
                    self._remove_user(chat_id, user['id'])

    def _new_user_callback(self, update, context):
        """ Add a new user into to_introduce list """
        logger.info("New users added!")
        self.config.to_introduce[update.message.chat.id] = []
        self.config.violations[update.message.chat.id] = {}
        for new_member in update.message.new_chat_members:
            user_name = new_member.username or new_member.first_name
            self.config.to_introduce[update.message.chat.id].append({"id": new_member.id,
                                                                     "name": new_member.username or new_member.first_name,
                                                                     "ban_at": time.time() + 60 * 60 * 24})
            self.config.violations[update.message.chat.id][new_member.id] = 0
            self.bot.sendMessage(update.message.chat.id, "Добро пожаловать, @{}!\n"
                                                         "Сначала представься с хештегом #whois за 5 слов и больше, "
                                                         "чтобы мы знали, кто ты ☺️".format(user_name))

    def _removed_user_callback(self, update, context):
        """ If the deleted user hasn't introduced yet, remove them """
        logger.info("Users deleted!")
        removed_member_id = update.message.left_chat_member.id
        self._remove_user(update.message.chat.id, removed_member_id)

    def _error_callback(self, update, context):
        logger.warning('Update "%s" caused error "%s"', update, context.error)

    def setup_scheduler(self):
        self.scheduler.add_job(self._autoban_callback, 'interval', hours=4)
        self.scheduler.start()

    def start(self):
        """ Set up and start the bot """
        self.updater.dispatcher.add_handler(CommandHandler("start", self._start))
        self.updater.dispatcher.add_handler(CommandHandler("help", self._help))
        self.updater.dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.status_update),
                                                           self._gatekeep_callback))
        self.updater.dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members,
                                                           self._new_user_callback), group=1)
        self.updater.dispatcher.add_handler(MessageHandler(Filters.status_update.left_chat_member,
                                                           self._removed_user_callback), group=2)
        self.updater.dispatcher.add_error_handler(self._error_callback)

        self.updater.start_webhook(listen="0.0.0.0",
                                   port=self.config.PORT,
                                   url_path=self.config.token,
                                   webhook_url="whois-gatekeeper.herokuapp.com/" + self.config.token)
        # self.updater.start_polling()
        self.updater.idle()


def main():
    """ Set up a bot from a configuration file and start it """

    bot_file = "config.json"
    bot = GatekeeperBot(bot_file)
    bot.setup_scheduler()
    bot.start()


if __name__ == '__main__':
    main()
