from .config import bot, logger, to_introduce, violations, seen_users
from .utils import remove_user, warn_user
import time


def gatekeep_callback(update, context):
    """ Manage messages based on #whois state """
    message_text = update.message.text or "a"
    message_id = update.message.message_id
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    user_name = update.message.from_user.username or update.message.from_user.first_name
    """ Remove any non-#whois message from a new user / 24h ban user for 3 violations """
    logger.info("User %s (%s) said: %s" % (user_name,
                                           update.message.from_user.id, update.message.text))

    if chat_id in to_introduce:
        if any([user['id'] == user_id for user in to_introduce[chat_id]]):
            if "#whois" in message_text and len(message_text.replace("#whois", "").strip()) > 13:
                remove_user(chat_id, user_id)

            elif violations[chat_id].get(user_id, 0) < 2:
                warning = warn_user(update)
                if "#whois" not in message_text or len(message_text.split()) - 1 < 5:
                    bot.sendMessage(chat_id, warning + "\nСначала познакомься со мной в личке.\n@who_ru_bot.")
            else:
                remove_user(chat_id, user_id)
                bot.deleteMessage(chat_id, message_id)
                bot.sendMessage(chat_id, "Я предупреждал, @{}!  Посиди-ка в бане сутки 😊".
                                format(user_name))
                banned_until = time.time() + 60 * 60 * 24
                bot.banChatMember(chat_id, user_id,
                                  until_date=banned_until)


def remove_users_callback(update, context):
    """ If the deleted user hasn't introduced yet, remove them """
    logger.info("Users deleted!")
    removed_member_id = update.message.left_chat_member.id
    remove_user(update.message.chat.id, removed_member_id)


def new_user_callback(update, context):
    """ Add a new user into to_introduce list """
    logger.info("New users added!")
    to_introduce[update.message.chat.id] = []
    violations[update.message.chat.id] = {}
    for new_member in update.message.new_chat_members:
        user_name = new_member.username or new_member.first_name
        if user_name != "who_ru_bot":
            sent_message = bot.sendMessage(update.message.chat.id, "Добро пожаловать, @{}!\n"
                                                                   "Прежде, чем писать сюда, напиши мне в личку.\n"
                                                                   "@who_ru_bot. Давай познакомимся ☺️".format(user_name))
            to_introduce[update.message.chat.id].append({"id": new_member.id,
                                                         "name": new_member.username or new_member.first_name,
                                                         "ban_at": time.time() + 60 * 60 * 24,
                                                         "greeting_id": sent_message.message_id})
            violations[update.message.chat.id][new_member.id] = 0
            seen_users[new_member.id][update.message.chat.title] = update.message.chat.id
        else:
            bot.sendMessage(update.message.chat.id, "#whois Всем привет!\b"
                                                    "Буду задавать вопросы всем новоприбывшим.\n"
                                                    "Пока список вопросов захардкожен, но скоро админ "
                                                    "сможет их настраивать. Ждите новых апдейтов :)\n"
                                                    "P.S. Не забудьте сделать меня админом!")


