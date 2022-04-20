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


def set_language(function):
    """ Create a user if they don't exist yet. Then make a language. """
    def set_language(*args, **kwargs):
        update = args[0]
        user_id = update.message.from_user.id
        username = get_username(update)

        if update.message.chat.id != update.message.from_user.id:
            # if command is in the wrong chat remove it
            bot.deleteMessage(update.message.chat.id,
                              update.message.message_id)
            return ConversationHandler.END

        new_user(user_id, username)  # if the user is not yet in database add them

        user_data = users.find_one(filter={"_id": str(user_id)})

        if "lang" not in user_data:  # if the language is not yet set
            new_user(user_id, username)
            keyboard = [
                [
                    InlineKeyboardButton("English", callback_data="en"),
                    InlineKeyboardButton("Русский", callback_data="ru")
                ]
            ]
            lang_markup = InlineKeyboardMarkup(keyboard)

            update.message.reply_text("Язык / Language ?",
                                      reply_markup=lang_markup)
            return ConversationHandler.END

        return function(*args, **kwargs)
    return set_language
