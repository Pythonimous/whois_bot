import time

import telegram
from pymongo.collection import ReturnDocument

from .base import get_chat_user, user_leaves_chat
from .config import bot, logger, chats, users, i18n

"""
def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)
"""


def get_username(update):
    if update.message.from_user.username:
        username = "@" + update.message.from_user.username
    else:
        username = update.message.from_user.first_name
    return username


def introduce_user(chat_id, user_id, locale):
    user_data = get_chat_user(chat_id, user_id)
    info_dict = user_data["chats"][chat_id]["info"]
    info_dict["username"] = user_data["username"]
    to_send = make_intro(info_dict, locale)
    bot.deleteMessage(chat_id, user_data["chats"][str(chat_id)]["greeting_id"])
    message = bot.sendMessage(chat_id, to_send, parse_mode=telegram.ParseMode.HTML)
    users.update_one(filter={"_id": user_data["_id"]},
                     update={"$unset": {"now_introducing": 1,
                                        f"chats.{chat_id}.ban_at": 1},
                             "$set": {f"chats.{message.chat.id}.greeting_id": message.message_id,
                                      f"chats.{chat_id}.need_intro": 0,
                                      f"chats.{chat_id}.violations": 0}})


def capfirst(string):
    # capitalize() lowercases all the other characters, and we don't want that
    return string[:1].upper() + string[1:] if string else ''


def lowfirst(string):
    return string[:1].lower() + string[1:] if string else ''


def make_intro(info_dict, locale):
    message = i18n.t(
        "callbacks.intro_message",
        username=info_dict['username'],
        name=info_dict["name"],
        came_from=info_dict['from'],
        age=info_dict['age'],
        specialty=capfirst(info_dict['specialty']),
        experience=info_dict['years_experience'],
        stack=info_dict['stack'],
        recent_project=lowfirst(info_dict['recent_project']),
        hobby=lowfirst(info_dict['hobby']),
        hobby_partners=i18n.t("callbacks.hobby_partners", locale=locale) if info_dict["hobby_partners"] else ".",
        in_antalya=lowfirst(info_dict['in_antalya']),
        looking_for_job=i18n.t("callbacks.looking_for_job", locale=locale) if info_dict["looking_for_job"] else "\n",
        locale=locale
    )
    return message


def warn_user(update, locale):
    """ Warn user of their 1st / 2nd #whois violation """
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    username = get_username(update)
    bot.deleteMessage(update.message.chat.id, update.message.message_id)

    user_data = users.find_one_and_update(filter={
        "_id": str(user_id),
        f"chats.{str(chat_id)}": {"$exists": True}},
        update={"$inc": {f"chats.{str(chat_id)}.violations": 1}},
        return_document=ReturnDocument.AFTER
    )

    if user_data["chats"][str(chat_id)]["violations"] == 1:
        return i18n.t("callbacks.warning_one",
                      name=username,
                      locale=locale)
    elif user_data["chats"][str(chat_id)]["violations"] == 2:
        return i18n.t("callbacks.warning_two",
                      name=username,
                      locale=locale)


def ban_user():
    """ Automatically ban users that haven't introduced themselves in 24 hours """
    current_time = time.time()
    for chat in chats.find():
        for user in users.find():
            if chat["_id"] in user["chats"]:
                if "ban_at" in user["chats"][chat["_id"]]:
                    if user["chats"][chat["_id"]]["ban_at"] <= current_time:
                        bot.sendMessage(
                            chat["_id"],
                            f"Banned {user['username']} for 3 days "
                            f"(no #whois in 24 hours)")
                        banned_until = current_time + 60 * 60 * 24 * 3
                        bot.banChatMember(chat["_id"], user["_id"],
                                          until_date=banned_until)
                        user_leaves_chat(chat["_id"], user["_id"])
