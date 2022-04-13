import time

import telegram
from pymongo.collection import ReturnDocument

from .base import get_chat_user, user_leaves_chat
from .config import bot, logger, chats, users


def error(update, context):
    """ Log errors in the console """
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def get_username(update):
    if update.message.from_user.username:
        username = "@" + update.message.from_user.username
    else:
        username = update.message.from_user.first_name
    return username


def introduce_user(chat_id, user_id):
    user_data = get_chat_user(chat_id, user_id)
    info_dict = user_data["chats"][chat_id]["info"]
    info_dict["username"] = user_data["username"]
    to_send = make_intro(info_dict)
    bot.deleteMessage(chat_id, user_data["chats"][str(chat_id)]["greeting_id"])
    bot.sendMessage(chat_id, to_send, parse_mode=telegram.ParseMode.HTML)
    users.update_one(filter={"_id": user_id},
                     update={
                         "$unset": {"now_introducing": 1,
                                    f"chats.{chat_id}.greeting_id": 1,
                                    f"chats.{chat_id}.ban_at": 1},
                         "$set": {f"chats.{chat_id}.need_intro": 0,
                                  f"chats.{chat_id}.violations": 0}
                     })


def capfirst(string):  # capitalize() lowercases all the other characters, and we don't want that
    return string[:1].upper() + string[1:] if string else ''


def lowfirst(string):
    return string[:1].lower() + string[1:] if string else ''


def make_intro(info_dict):
    message = f"#whois {info_dict['username']}\n"
    message += f"🎉 К нам присоединился <b>{info_dict['name']} ({info_dict['from']})</b>, "
    message += f"{info_dict['age']} лет от роду 🎊\n"
    message += f"{capfirst(info_dict['specialty'])} со стажем {info_dict['years_experience']} лет.\n"
    message += f"Стек технологий: {info_dict['stack']}.\n"
    message += f"На последнем проекте {info_dict['recent_project']}.\n"
    message += f"Любит {info_dict['hobby']}"
    if info_dict["hobby_partners"]: message += "; ищет товарищей по хобби"
    message += ".\n"
    message += f"В Анталии {lowfirst(info_dict['in_antalya'])}.\n"
    if info_dict["looking_for_job"]: message += "В поиске работы.\n"
    message += '\n'
    message += "Добро пожаловать!"
    return message


def warn_user(update):
    """ Warn user of their 1st / 2nd #whois violation """
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    username = get_username(update)
    bot.deleteMessage(update.message.chat.id, update.message.message_id)

    user_data = users.find_one_and_update(filter={
        "_id": str(user_id),
        f"chats.{str(chat_id)}": {"$exists": True}},
        update={
            "$inc": {f"chats.{str(chat_id)}.violations": 1}
        }, return_document=ReturnDocument.AFTER
    )
    print(user_data)

    if user_data["chats"][str(chat_id)]["violations"] == 1:
        return "Ошибочка вышла, @{}!".format(username)
    elif user_data["chats"][str(chat_id)]["violations"] == 2:
        return "Не испытывай моё терпение, @{}!".format(username)


def ban_user():
    """ Automatically ban users that haven't introduced themselves in 24 hours """
    current_time = time.time()
    for chat in chats.find():
        for user in users.find():
            if chat["_id"] in user["chats"]:
                if "ban_at" in user["chats"][chat["_id"]]:
                    if user["chats"][chat["_id"]]["ban_at"] <= current_time:
                        bot.sendMessage(chat["_id"], f"Banned {user['username']} for a week (no #whois in 24 hours)")
                        banned_until = current_time + 60 * 60 * 24 * 7
                        bot.banChatMember(chat["_id"], user["_id"], until_date=banned_until)
                        user_leaves_chat(chat["_id"], user["_id"])
