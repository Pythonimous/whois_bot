#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""bot.py: A Telegram bot to gatekeep your server"""

__author__ = "Pythonimous"


import os

from apscheduler.schedulers.background import BackgroundScheduler

from telegram.ext import Updater, MessageHandler, CommandHandler, Filters, ConversationHandler

from whoisbot.utils import error, ban_user
from whoisbot.conversation import help, start, cancel
from whoisbot.conversation import (
    chat,
    name,
    age,
    howlongantalya,
    specialty,
    experience,
    stack,
    recent_projects,
    hobby,
    looking_for_job,
    end_convo
)
from whoisbot.callbacks import gatekeep_callback, remove_users_callback, new_user_callback


class GatekeeperBot:
    """
    A bot that requires people to introduce themselves using #whois first.
    The bot bans people for 24h after failure to do so 3 times.
    """
    def __init__(self):
        self.token = os.environ.get('BOT_TOKEN')
        self.updater = Updater(self.token, use_context=True)

    def start_bot(self):
        """ Set up and start the bot """
        self.updater.dispatcher.add_handler(CommandHandler("help", help))

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", start)],
            states={
                0: [MessageHandler(Filters.text, chat)],
                1: [MessageHandler(Filters.text, name)],
                2: [MessageHandler(Filters.text, age)],
                3: [MessageHandler(Filters.text, howlongantalya)],
                4: [MessageHandler(Filters.text, specialty)],
                5: [MessageHandler(Filters.text, experience)],
                6: [MessageHandler(Filters.text, stack)],
                7: [MessageHandler(Filters.text, recent_projects)],
                8: [MessageHandler(Filters.text, hobby)],
                9: [MessageHandler(Filters.text, looking_for_job)],
                10: [MessageHandler(Filters.text, end_convo)],
            },
            fallbacks=[CommandHandler('cancel', cancel)],
        )

        self.updater.dispatcher.add_handler(conv_handler)

        self.updater.dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.status_update),
                                                           gatekeep_callback))
        self.updater.dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members,
                                                           new_user_callback), group=1)
        self.updater.dispatcher.add_handler(MessageHandler(Filters.status_update.left_chat_member,
                                                           remove_users_callback), group=2)

        self.updater.dispatcher.add_error_handler(error)
        self.updater.start_polling()
        self.updater.idle()


def main():
    """ Set up a bot from a configuration file and start it """
    bot = GatekeeperBot()
    scheduler = BackgroundScheduler()
    scheduler.add_job(ban_user, 'interval', hours=4)
    scheduler.start()
    bot.start_bot()


if __name__ == "__main__":
    main()
