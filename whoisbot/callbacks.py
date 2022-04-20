import time
import telegram

from .base import new_chat, new_user, \
    user_joins_chat, get_chat_user, \
    user_leaves_chat, bot_leaves_chat
from .config import bot, logger, users, i18n
from .decorators import chatname_changes, username_changes
from .utils import warn_user, get_username


@chatname_changes
@username_changes
def gatekeep_callback(update, _):
    """ Manage messages based on #whois state """
    message_id = update.message.message_id
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    username = get_username(update)

    """ Remove any non-#whois message from a new user / 
    24h ban user for 3 violations """
    logger.info("User %s (%s) said: %s" % (username,
                                           update.message.from_user.id,
                                           update.message.text))

    user_data = get_chat_user(chat_id, user_id)
    if user_data:
        lang = user_data["lang"]
        if user_data["chats"][str(chat_id)]["need_intro"] == 1:
            if user_data["chats"][str(chat_id)]["violations"] < 2:
                warning = warn_user(update, lang)
                bot.sendMessage(
                    user_id,
                    warning + "\n" + i18n.t("callbacks.warning_end",
                                            locale=lang)
                )
            else:
                user_leaves_chat(chat_id, user_id)
                bot.deleteMessage(chat_id, message_id)
                bot.sendMessage(
                    user_id,
                    i18n.t("callbacks.ban_spam",
                           name=username,
                           locale=lang)
                )
                banned_until = time.time() + 60 * 60 * 24 * 3
                bot.banChatMember(chat_id, user_id,
                                  until_date=banned_until)


@chatname_changes
def remove_users_callback(update, _):
    """ If the deleted user hasn't introduced yet, remove them """
    logger.info("Users deleted!")

    username = update.message.left_chat_member.first_name
    if update.message.left_chat_member.username:
        username = "@" + update.message.left_chat_member.username

    if username not in {"@who_ru_bot", "@whoisit_test_bot"}:
        user_leaves_chat(update.message.chat.id,
                         update.message.left_chat_member.id)
    else:
        bot_leaves_chat(update.message.chat.id)


@chatname_changes
def new_user_callback(update, _):
    """ Add a new user into base list """
    logger.info("New users added!")
    for new_member in update.message.new_chat_members:
        # if the user had been deleted but no chat callback seen
        if get_chat_user(update.message.chat.id, new_member.id):
            user_leaves_chat(update.message.chat.id, new_member.id)
        username = new_member.first_name

        if new_member.username:
            username = "@" + new_member.username

        if username not in {"@who_ru_bot", "@whoisit_test_bot"}:

            if not users.count_documents({'_id': str(new_member.id)}):
                new_user(new_member.id, username)

            greeting_msg = i18n.t("callbacks.user_joins", username=username,
                                  locale='ru') \
                           + '\n' \
                           + i18n.t("callbacks.user_joins", username=username,
                                    locale='en')

            sent_message = bot.sendMessage(
                update.message.chat.id,
                greeting_msg,
                parse_mode=telegram.ParseMode.HTML
            )

            user_joins_chat(update.message.chat.id, new_member.id)
            users.update_one(
                filter={"_id": str(new_member.id)},
                update={"$set": {
                    f"chats.{update.message.chat.id}.greeting_id":
                        sent_message.message_id,
                    f"chats.{update.message.chat.id}.ban_at":
                        time.time() + 60 * 60 * 24}}
            )

        else:
            new_chat(update.message.chat.id, update.message.chat.title)
            message_text = "#whois @who_ru_bot\n"
            message_text += i18n.t("callbacks.bot_joins", locale='ru')
            message_text += "\n"
            message_text += i18n.t("callbacks.bot_joins", locale='en')
            bot.sendMessage(update.message.chat.id,
                            message_text)
