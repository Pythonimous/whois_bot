#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""bot.py: A Telegram bot to gatekeep your server"""

__author__ = "Pythonimous"


import os

from apscheduler.schedulers.background import BackgroundScheduler

from telegram.ext import Updater, MessageHandler, CommandHandler, Filters

from whoisbot.utils import error, ban_user
from whoisbot.private_msg import help, start
from whoisbot.callbacks import gatekeep_callback, remove_users_callback, new_user_callback


class GatekeeperBot:
    """
    A bot that requires people to introduce themselves using #whois first.
    The bot bans people for 24h after failure to do so 3 times.
    """
    def __init__(self):
        self.token = os.environ.get('BOT_TOKEN')
        self.updater = Updater(self.token, use_context=True)

    def start(self):
        """ Set up and start the bot """
        self.updater.dispatcher.add_handler(CommandHandler("start", start))
        self.updater.dispatcher.add_handler(CommandHandler("help", help))
        self.updater.dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.status_update),
                                                           gatekeep_callback))
        self.updater.dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members,
                                                           new_user_callback), group=1)
        self.updater.dispatcher.add_handler(MessageHandler(Filters.status_update.left_chat_member,
                                                           remove_users_callback), group=2)
        self.updater.dispatcher.add_error_handler(error)

        self.updater.start_webhook(listen="0.0.0.0",
                                   port=os.getenv('PORT', default=8443)
                                   url_path=self.token,
                                   webhook_url="https://stormy-eyrie-16859.herokuapp.com/" + self.token)

        #self.updater.start_polling()
        self.updater.idle()


def main():
    """ Set up a bot from a configuration file and start it """
    bot = GatekeeperBot()
    scheduler = BackgroundScheduler()
    scheduler.add_job(ban_user, 'interval', hours=4)
    scheduler.start()
    bot.start()


if __name__ == "__main__":
    main()
