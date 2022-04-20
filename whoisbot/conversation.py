from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ConversationHandler

from whoisbot.config import bot, users, chats, i18n
from whoisbot.utils import introduce_user
from whoisbot.decorators import set_language
from whoisbot.base import get_user

CHAT, RULES, NAME, AGE, WHERE_FROM, HOW_LONG_ANTALYA, SPECIALTY, EXPERIENCE,\
    STACK, RECENT_PROJECTS, HOBBY, HOBBY_PARTNERS, LOOKING_JOB = range(13)


@set_language
def start(update, _):
    """ /start command """
    user_data = users.find_one(
        filter={
            "_id": str(update.message.from_user.id)
        }
    )
    lang = user_data["lang"]

    if not user_data["chats"]:
        update.message.reply_text(
            i18n.t('convo.user_new', locale=lang)
        )
        return ConversationHandler.END

    chats_to_introduce = [chat_id
                          for chat_id, info in user_data["chats"].items()
                          if info["need_intro"]]

    if not chats_to_introduce:
        update.message.reply_text(
            i18n.t("convo.user_no_new_chats", locale=lang)
        )
        return ConversationHandler.END

    chat_names = [[chat["name"]]
                  for chat in chats.find({"_id": {"$in": chats_to_introduce}})]

    chats_markup = ReplyKeyboardMarkup(chat_names, one_time_keyboard=True)
    update.message.reply_text(
        i18n.t("convo.user_new_chats", locale=lang),
        reply_markup=chats_markup)
    return CHAT


def lang_button(update, _):
    query = update.callback_query
    query.answer()
    query.edit_message_text(i18n.t('convo.lang_choice', locale=query.data))
    users.update_one(
        filter={'_id': str(query.message.chat.id)},
        update={
            '$set': {"lang": query.data}
        }
    )


def chat(update, _):

    user_id = str(update.message.from_user.id)
    user_data = get_user(user_id)
    lang = user_data["lang"]
    chat = chats.find_one(filter={"name": update.message.text})
    if not chat:
        bot.sendMessage(
            update.message.from_user.id,
            i18n.t("convo.unknown_chat", locale=lang)
        )
        return CHAT
    if chat['_id'] not in user_data["chats"]:
        bot.sendMessage(
            update.message.from_user.id,
            i18n.t("convo.unknown_chat", locale=lang)
        )
        return CHAT
    else:
        users.update_one(
            filter={"_id": user_id},
            update={"$set": {"now_introducing": str(chat['_id'])}}
        )
        if not any(['test_whoisbot_2' in chat["name"],
                    'whois_test' in chat["name"],
                    "IT-pros of Anatolia" in chat["name"]]):
            bot.sendMessage(
                update.message.from_user.id,
                i18n.t("convo.name", locale=lang)
            )
            return NAME
        else:
            bot.sendMessage(update.message.from_user.id,
                            i18n.t("convo.chat_rules_lets", locale=lang))
            bot.sendMessage(update.message.from_user.id,
                            i18n.t("convo.chat_rules_text", locale=lang))
            bot.sendMessage(update.message.from_user.id,
                            i18n.t("convo.chat_rules_confirm", locale=lang))
            return RULES


def rules(update, _):
    user_id = str(update.message.from_user.id)
    lang = get_user(user_id)["lang"]

    if update.message.text.strip().lower() not in {"редиска", "radish"}:
        update.message.reply_text(i18n.t("convo.chat_rules_wrong_password",
                                         locale=lang))
        return RULES
    bot.sendMessage(
        update.message.from_user.id,
        i18n.t("convo.name", locale=lang)
    )
    return NAME


def name(update, _):
    # определяем пользователя
    user_id = str(update.message.from_user.id)
    user_data = get_user(user_id)
    chat_id = user_data["now_introducing"]
    lang = user_data["lang"]

    users.update_one(
        filter={"_id": user_id},
        update={"$set": {f"chats.{chat_id}.info.name": update.message.text}}
    )

    update.message.reply_text(
        i18n.t("convo.age_ok", locale=lang),
        reply_markup=ReplyKeyboardRemove(),
    )
    return AGE


def age(update, _):
    user_id = str(update.message.from_user.id)
    user_data = get_user(user_id)
    lang = user_data["lang"]
    try:
        chat_id = user_data["now_introducing"]
        users.update_one(
            filter={"_id": user_id},
            update={"$set": {
                f"chats.{chat_id}.info.age": int(update.message.text.strip())}
            }
        )
        update.message.reply_text(
            i18n.t("convo.location", locale=lang)
        )
        return WHERE_FROM
    except ValueError:
        update.message.reply_text(
            i18n.t("convo.age_wrong_format", locale=lang)
        )
        return AGE


def wherefrom(update, _):
    user_id = str(update.message.from_user.id)
    user_data = get_user(user_id)
    chat_id = user_data["now_introducing"]
    lang = user_data["lang"]
    users.update_one(
        filter={"_id": user_id},
        update={"$set": {f"chats.{chat_id}.info.from": update.message.text}})
    update.message.reply_text(
        i18n.t("convo.how_long_antalya", locale=lang)
    )
    return HOW_LONG_ANTALYA


def howlongantalya(update, _):
    user_id = str(update.message.from_user.id)
    user_data = get_user(user_id)
    chat_id = user_data["now_introducing"]
    lang = user_data["lang"]
    users.update_one(
        filter={"_id": user_id},
        update={
            "$set": {f"chats.{chat_id}.info.in_antalya": update.message.text}
        }
    )
    update.message.reply_text(
        i18n.t("convo.specialty", locale=lang)
    )
    return SPECIALTY


def specialty(update, _):
    user_id = str(update.message.from_user.id)
    user_data = get_user(user_id)
    chat_id = user_data["now_introducing"]
    lang = user_data["lang"]
    users.update_one(
        filter={"_id": user_id},
        update={
            "$set": {f"chats.{chat_id}.info.specialty": update.message.text}
        }
    )
    update.message.reply_text(
        i18n.t("convo.years_experience_ok", locale=lang)
    )
    return EXPERIENCE


def experience(update, _):
    user_id = str(update.message.from_user.id)
    user_data = get_user(user_id)
    chat_id = user_data["now_introducing"]
    lang = user_data["lang"]
    try:
        users.update_one(
            filter={"_id": user_id},
            update={
                "$set": {f"chats.{chat_id}.info.years_experience":
                         int(update.message.text.strip())}}
        )
        update.message.reply_text(
            i18n.t("convo.stack", locale=lang)
        )
        return STACK
    except ValueError:
        update.message.reply_text(
            i18n.t("convo.years_experience_wrong_format", locale=lang)
        )
        return EXPERIENCE


def stack(update, _):
    user_id = str(update.message.from_user.id)
    user_data = get_user(user_id)
    chat_id = user_data["now_introducing"]
    lang = user_data["lang"]
    users.update_one(
        filter={"_id": user_id},
        update={"$set": {f"chats.{chat_id}.info.stack": update.message.text}})
    update.message.reply_text(
        i18n.t("convo.recent_project", locale=lang)
    )
    return RECENT_PROJECTS


def recent_projects(update, _):
    text = update.message.text

    user_id = str(update.message.from_user.id)
    user_data = get_user(user_id)

    lang = user_data["lang"]

    if len(text.split()) < 25:
        update.message.reply_text(
            i18n.t("convo.recent_project_short", locale=lang)
        )
        return RECENT_PROJECTS

    chat_id = user_data["now_introducing"]
    users.update_one(
        filter={"_id": user_id},
        update={"$set": {f"chats.{chat_id}.info.recent_project": text}}
    )
    update.message.reply_text(
        i18n.t("convo.hobbies", locale=lang)
    )
    return HOBBY


def hobby(update, _):
    user_id = str(update.message.from_user.id)
    user_data = get_user(user_id)
    chat_id = user_data["now_introducing"]
    lang = user_data["lang"]

    users.update_one(
        filter={"_id": user_id},
        update={"$set": {f"chats.{chat_id}.info.hobby": update.message.text}}
    )
    reply_keyboard = [
        [
            "Yes",
            "No"
        ]
    ]
    markup_key = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text(
        i18n.t("convo.hobby_partners", locale=lang),
        reply_markup=markup_key
    )
    return HOBBY_PARTNERS


# TODO: Make it inline markup
def hobby_partners(update, _):
    user_id = str(update.message.from_user.id)
    user_data = get_user(user_id)
    chat_id = user_data["now_introducing"]
    lang = user_data["lang"]

    if update.message.text.lower().strip() in ['да', 'yes']:
        users.update_one(
            filter={"_id": user_id},
            update={"$set": {f"chats.{chat_id}.info.hobby_partners": 1}}
        )
    else:
        users.update_one(
            filter={"_id": user_id},
            update={"$set": {f"chats.{chat_id}.info.hobby_partners": 0}}
        )
    reply_keyboard = [["Yes", "No"]]
    markup_key = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text(
        i18n.t("convo.looking_for_job", locale=lang),
        reply_markup=markup_key
    )
    return LOOKING_JOB


def looking_job(update, _):

    user_id = str(update.message.from_user.id)
    user_data = get_user(user_id)
    chat_id = user_data["now_introducing"]
    lang = user_data["lang"]

    if update.message.text.lower().strip() in ['да', 'yes']:
        users.update_one(
            filter={"_id": str(update.message.from_user.id)},
            update={"$set": {f"chats.{chat_id}.info.looking_for_job": 1}}
        )
    else:
        users.update_one(
            filter={"_id": str(update.message.from_user.id)},
            update={"$set": {f"chats.{chat_id}.info.looking_for_job": 0}}
        )

    update.message.reply_text(
        i18n.t("convo.intro_over", locale=lang),
        reply_markup=ReplyKeyboardRemove()
    )
    bot.sendMessage(
        update.message.chat.id,
        i18n.t("convo.sellout", locale=lang)
    )

    introduce_user(chat_id, user_id)

    return ConversationHandler.END


@set_language
def cancel(update, _):
    user_id = str(update.message.from_user.id)
    user_data = get_user(user_id)
    lang = user_data["lang"]

    update.message.reply_text(
        i18n.t("convo.cancel", locale=lang),
        reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


@set_language
def info(update, _):
    """ /info command """
    user_id = str(update.message.from_user.id)
    user_data = get_user(user_id)
    lang = user_data["lang"]

    bot.sendMessage(
        update.message.chat.id,
        i18n.t("convo.info", locale=lang)
    )


@set_language
def help(update, _):
    """ /help command """
    user_id = str(update.message.from_user.id)
    user_data = get_user(user_id)
    lang = user_data["lang"]

    bot.sendMessage(
        update.message.chat.id,
        i18n.t("convo.help", locale=lang)
    )
