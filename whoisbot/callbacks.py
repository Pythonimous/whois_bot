import time
import telegram

from .base import new_chat, new_user, user_joins_chat, get_chat_user, user_leaves_chat, bot_leaves_chat
from .config import bot, logger, users
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

    """ Remove any non-#whois message from a new user / 24h ban user for 3 violations """
    logger.info("User %s (%s) said: %s" % (username,
                                           update.message.from_user.id, update.message.text))

    user_data = get_chat_user(chat_id, user_id)
    if user_data:
        if user_data["chats"][str(chat_id)]["need_intro"] == 1:
            if user_data["chats"][str(chat_id)]["violations"] < 2:
                warning = warn_user(update)
                bot.sendMessage(user_id, warning + "\nСначала познакомься со мной в личке.\n@who_ru_bot.")
            else:
                user_leaves_chat(chat_id, user_id)
                bot.deleteMessage(chat_id, message_id)
                bot.sendMessage(user_id, "Я предупреждал, {}!  Посиди-ка в бане сутки 😊".
                                format(username))
                banned_until = time.time() + 60 * 60 * 24
                bot.banChatMember(chat_id, user_id,
                                  until_date=banned_until)


@chatname_changes
def remove_users_callback(update, _):
    """ If the deleted user hasn't introduced yet, remove them """
    logger.info("Users deleted!")

    username = update.message.left_chat_member.first_name
    if update.message.left_chat_member.username:
        username = "@" + update.message.left_chat_member.username

    if username != "@who_ru_bot":
        user_leaves_chat(update.message.chat.id, update.message.left_chat_member.id)
    else:
        bot_leaves_chat(update.message.chat.id)


@chatname_changes
def new_user_callback(update, _):
    """ Add a new user into base list """
    logger.info("New users added!")
    for new_member in update.message.new_chat_members:
        if get_chat_user(update.message.chat.id, new_member.id):  # if user was deleted before
            user_leaves_chat(update.message.chat.id, new_member.id)
        username = new_member.first_name
        if new_member.username:
            username = "@" + new_member.username

        if username not in {"@who_ru_bot", "@whoisit_test_bot"}:
            sent_message = bot.sendMessage(update.message.chat.id,
                                           "Добро пожаловать, {}! Давай познакомимся ☺\n"
                                           "Прежде, чем общаться в чате - необходимо "
                                           "представиться и рассказать о себе.\n"
                                           "Для этого напиши мне в личку (@who_ru_bot) "
                                           "команду <code>/start</code> (у тебя есть 24ч; потом запрет "
                                           "на доступ в чат на 3 дня)".format(username),
                                           parse_mode=telegram.ParseMode.HTML)

            if not users.count_documents({'_id': str(new_member.id)}):
                new_user(new_member.id, username)

            user_joins_chat(update.message.chat.id, new_member.id)
            users.update_one(filter={"_id": str(new_member.id)},
                             update={"$set": {f"chats.{update.message.chat.id}.greeting_id": sent_message.message_id,
                                              f"chats.{update.message.chat.id}.ban_at": time.time() + 60 * 60 * 24}})

        else:
            new_chat(update.message.chat.id, update.message.chat.title)
            bot.sendMessage(update.message.chat.id, "#whois Всем привет!\b"
                                                    "Буду задавать вопросы всем новоприбывшим.\n"
                                                    "Пока список вопросов захардкожен, но скоро админ "
                                                    "сможет их настраивать. Ждите новых апдейтов :)\n"
                                                    "P.S. Не забудьте сделать меня админом!")
