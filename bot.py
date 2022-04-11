#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""bot.py: A Telegram bot to gatekeep your server"""

__author__ = "Pythonimous"

from apscheduler.schedulers.background import BackgroundScheduler
from telegram.ext import Updater, MessageHandler, CommandHandler, Filters, ConversationHandler

from whoisbot.callbacks import gatekeep_callback, remove_users_callback, new_user_callback
from whoisbot.config import token
from whoisbot.conversation import (
    chat, CHAT,
    name, NAME,
    age, AGE,
    howlongantalya, HOW_LONG_ANTALYA,
    specialty, SPECIALTY,
    experience, EXPERIENCE,
    stack, STACK,
    recent_projects, RECENT_PROJECTS,
    hobby, HOBBY,
    hobby_partners, HOBBY_PARTNERS,
    looking_job, LOOKING_JOB
)
from whoisbot.conversation import help, start, cancel
from whoisbot.utils import error, ban_user


class GatekeeperBot:
    """
    A bot that requires people to introduce themselves using #whois first.
    The bot bans people for 24h after failure to do so 3 times.
    """
    def __init__(self):

        self.updater = Updater(token, use_context=True)

    def start_bot(self):
        """ Set up and start the bot """
        self.updater.dispatcher.add_handler(CommandHandler("help", help))

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", start)],
            states={
                CHAT: [MessageHandler(Filters.text, chat)],
                NAME: [MessageHandler(Filters.text, name)],
                AGE: [MessageHandler(Filters.text, age)],
                HOW_LONG_ANTALYA: [MessageHandler(Filters.text, howlongantalya)],
                SPECIALTY: [MessageHandler(Filters.text, specialty)],
                EXPERIENCE: [MessageHandler(Filters.text, experience)],
                STACK: [MessageHandler(Filters.text, stack)],
                RECENT_PROJECTS: [MessageHandler(Filters.text, recent_projects)],
                HOBBY: [MessageHandler(Filters.text, hobby)],
                HOBBY_PARTNERS: [MessageHandler(Filters.text, hobby_partners)],
                LOOKING_JOB: [MessageHandler(Filters.text, looking_job)],
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
    scheduler.add_job(ban_user, 'interval', hours=24)
    scheduler.start()
    bot.start_bot()


if __name__ == "__main__":
    main()
