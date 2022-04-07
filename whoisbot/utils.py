from .config import bot, to_introduce, violations, logger
import time


def error(update, context):
    """ Log errors in the console """
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def remove_user(chat_id, user_id):
    """ Remove user from to_introduce and violations lists """
    if chat_id in to_introduce:
        for user in to_introduce[chat_id]:
            if user['id'] == user_id:
                to_introduce[chat_id].remove(user)
                break
    if chat_id in violations:
        if user_id in violations[chat_id]:
            del violations[chat_id][user_id]


def warn_user(update):
    """ Warn user of their 1st / 2nd #whois violation """
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    user_name = update.message.from_user.username or update.message.from_user.first_name
    bot.deleteMessage(update.message.chat.id, update.message.message_id)
    violations[chat_id][user_id] += 1
    if violations[chat_id].get(user_id, 0) == 1:
        return "Ошибочка вышла, @{}!".format(user_name)
    elif violations[chat_id].get(user_id, 0) == 2:
        return "Не испытывай моё терпение, @{}!".format(user_name)


def ban_user():
    """ Automatically ban users that haven't introduced themselves in 24 hours """
    current_time = time.time()
    for chat_id in to_introduce:
        for user in to_introduce[chat_id]:
            if current_time >= user['ban_at']:
                bot.sendMessage(chat_id, f"Banned {user['name']} for a week (no #whois in 24 hours)")
                banned_until = current_time + 60 * 60 * 24 * 7
                bot.banChatMember(chat_id, user['id'],
                                  until_date=banned_until)
                remove_user(chat_id, user['id'])
