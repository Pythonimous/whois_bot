#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""bot.py: A Telegram bot to gatekeep your serverr"""

__author__ = "Pythonimous"


from telegram.ext import Updater, MessageHandler, CommandHandler, Filters
from telegram import Bot
import logging
import json

import time
import os

import sys
from glob import glob

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
        self.PORT = int(os.environ.get('PORT', '8443'))
        self.admins = self.config["admins"]
        self.to_introduce = []
        self.violations = {}
        logger.info('Loaded bot:\n"%s"' % (json.dumps(self.config, indent=4, separators=(',', ': '))))
        return


class GatekeeperBot:
    """ A class defining the bot behaviour.
        The bot answers commands added with the add_command method using a callback function.
        Non command messages are treated depending on the mode the bot is set (with respect to the user).
        Modes are added with the add_chat_mode, and commands' callback may set them calling the set_chat_mode method.
    """

    def __init__(self, file_path):
        self.config = BotConfig(file_path)
        self.updater = Updater(self.config.token, use_context=True)
        self.dispatcher = self.updater.dispatcher
        self.bot = Bot(self.config.token)

    def _warn_user(self, update):
        """ Warn user of their 1st / 2nd #whois violation """
        user_id = update.message.from_user.id
        user_name = update.message.from_user.first_name
        self.bot.deleteMessage(update.message.chat.id, update.message.message_id)
        self.config.violations[user_id] += 1
        if self.config.violations.get(user_id, 0) == 1:
            return "Привет, {}!".format(user_name)
        elif self.config.violations.get(user_id, 0) == 2:
            return "Не испытывай моё терпение, {}!".format(user_name)

    def _gatekeep_callback(self, update, context):
        """ Remove any non-#whois message from a new user / 24h ban user for 3 violations """
        logger.info("User %s (%s) said: %s" % (update.message.from_user.first_name,
                                               update.message.from_user.id, update.message.text))

        message_text = update.message.text or "a"
        chat_id = update.message.chat.id
        user_id = update.message.from_user.id
        user_firstname = update.message.from_user.first_name

        if user_id in self.config.to_introduce and user_id not in self.config.admins:
            if "#whois" in message_text and len(message_text.replace("#whois", "").strip()) > 13:
                self.config.to_introduce.remove(user_id)
                del self.config.violations[user_id]

            elif self.config.violations.get(user_id, 0) < 2:
                warning = self._warn_user(update)
                if "#whois" not in message_text or len(message_text.split()) - 1 < 5:
                    self.bot.sendMessage(chat_id, warning + "\nСначала представься за 5+ слов с хештегом #whois.".
                                                            format(user_firstname))
            else:
                self.config.to_introduce.remove(user_id)
                del self.config.violations[user_id]
                self.bot.sendMessage(chat_id, "Я предупреждал, {}! Попробуешь ещё через 24 часа.".
                                              format(user_firstname))
                banned_until = time.time() + 60 * 60 * 24
                self.bot.banChatMember(chat_id, user_id,
                                       until_date=banned_until)

    def _start(self, update, context):
        self.bot.sendMessage(update.message.chat.id, "Привет! Просто добавь меня в чат, и я сделаю всё сам.")

    def _help(self, update, context):
        self.bot.sendMessage(update.message.chat.id, "Я работаю просто.\n"
                                                     "Каждый, кто заходит в МОЙ чат, должен представиться с #whois"
                                                     "за 5 слов и более. У него три попытки. Не смог? Бан на сутки :)\n"
                                                     "За дополнительным функционалом обращайтесь к моему автору: https://github.com/Pythonimous")

    def _new_user_callback(self, update, context):
        """ Add a new user into to_introduce list """
        logger.info("New users added!")
        for new_member in update.message.new_chat_members:
            self.config.to_introduce.append(new_member.id)
            self.config.violations[new_member.id] = 0

    def _removed_user_callback(self, update, context):
        """ If the deleted user hasn't introduced yet, remove them """
        logger.info("Users deleted!")
        removed_member_id = update.message.left_chat_member.id
        self.config.to_introduce.remove(removed_member_id)
        if removed_member_id in self.config.violations:
            del self.config.violations[removed_member_id]

    def _error_callback(self, update, context):
        logger.warning('Update "%s" caused error "%s"', update, context.error)

    def start(self):
        """ Set up and start the bot """
        self.updater.dispatcher.add_handler(CommandHandler("start", self._start))
        self.updater.dispatcher.add_handler(CommandHandler("help", self._help))
        self.updater.dispatcher.add_handler(MessageHandler(Filters.text, self._gatekeep_callback))
        self.updater.dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members,
                                                           self._new_user_callback))
        self.updater.dispatcher.add_handler(MessageHandler(Filters.status_update.left_chat_member,
                                                           self._removed_user_callback))
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
    bot.start()


if __name__ == '__main__':
    main()
