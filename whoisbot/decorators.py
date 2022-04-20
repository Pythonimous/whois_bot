from .base import new_chatname, new_username, new_user
from .config import chats, users, bot
from .utils import get_username
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler

def chatname_changes(function):
    def change_names(*args, **kwargs):
        """ Check for known chat name change """
        if not chats.count_documents(filter={'_id': args[0].message.chat.id, 'name': args[0].message.chat.title}):
            new_chatname(args[0].message.chat.id, args[0].message.chat.title)
        return function(*args, **kwargs)
    return change_names


def username_changes(function):
    def change_names(*args, **kwargs):
        """ Check for known user name changes """
        username = get_username(args[0])
        if users.count_documents(filter={'_id': args[0].message.from_user.id}):  # if we know the user
            if not users.count_documents({'_id': args[0].message.from_user.id, 'username': username}):  # under a different name
                new_username(args[0].message.from_user.id, username)
        return function(*args, **kwargs)
    return change_names


def verify_message(function):
    """ Remove a message if wrong chat,
    else create a user if they don't exist yet"""
    def verify_message(*args, **kwargs):
        update = args[0]
        user_id = update.message.from_user.id
        username = get_username(update)

        if update.message.chat.id != update.message.from_user.id:
            # if command is in the wrong chat remove it
            bot.deleteMessage(update.message.chat.id,
                              update.message.message_id)
            return ConversationHandler.END

        new_user(user_id, username)  # if the user is not yet in database add them

        return function(*args, **kwargs)
    return verify_message
