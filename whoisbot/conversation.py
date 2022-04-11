from whoisbot.config import bot, logger, users, chats
from whoisbot.utils import introduce_user
from telegram.ext import ConversationHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove

CHAT, NAME, AGE, HOW_LONG_ANTALYA, SPECIALTY, EXPERIENCE, STACK,\
RECENT_PROJECTS, HOBBY, HOBBY_PARTNERS, LOOKING_JOB = range(11)


def start(update, context):
    """ /start command """
    user_id = update.message.from_user.id
    if update.message.chat.id != update.message.from_user.id:
        bot.deleteMessage(update.message.chat.id, update.message.message_id)
        return ConversationHandler.END

    user_data = users.find_one(filter={"_id": str(user_id)})
    if not user_data:
        bot.sendMessage(user_id, "Привет! Просто добавь меня в чат, и я сделаю всё сам.\n"
                                 "ВАЖНО: НЕ ЗАБУДЬ сделать меня администратором 😉")
        return ConversationHandler.END

    else:
        user_chats = [chat_id for chat_id, info in user_data["chats"].items() if info["need_intro"]]
        chat_names = [chat["name"] for chat in chats.find({"_id": {"$in": user_chats}})]
        bot.sendMessage(user_id, f"Привет! Ты ещё не представился в чатах:\n"
                                 f"{'; '.join(chat_names)}.\n"
                                 f"В каком хочешь представиться?\n"
                                 f"Или /cancel, чтобы прекратить разговор.")
        return CHAT


def chat(update, context):
    if update.message.text.strip() == "/cancel":
        return cancel(update, context)
    user_id = str(update.message.from_user.id)
    user_data = users.find_one(filter={"_id": user_id})
    chat = chats.find_one(filter={"name": update.message.text})
    if not chat:
        bot.sendMessage(update.message.from_user.id, "Не знаю этот чат. Попробуй ещё раз!")
        return CHAT
    if chat['_id'] not in user_data["chats"]:
        bot.sendMessage(update.message.from_user.id, "Не знаю этот чат. Попробуй ещё раз!")
        return CHAT
    else:
        users.update_one(filter={"_id": user_id},
                         update={"$set": {"now_introducing": str(chat['_id'])}})
        bot.sendMessage(update.message.from_user.id, 'Хорошо! Как к тебе обращаться? '
                                                     'Назови имя, или никнейм, если больше нравится.')
        return NAME


def name(update, context):
    # определяем пользователя
    user_id = str(update.message.from_user.id)
    chat_id = users.find_one({"_id": user_id})["now_introducing"]
    users.update_one(filter={"_id": str(update.message.from_user.id)},
                     update={"$set": {f"chats.{chat_id}.info.name": update.message.text}})

    update.message.reply_text(
        'Хорошо! Сколько тебе лет? (напиши число)',
        reply_markup=ReplyKeyboardRemove(),
    )
    return AGE


def age(update, context):
    try:
        user_id = str(update.message.from_user.id)
        chat_id = users.find_one({"_id": user_id})["now_introducing"]
        users.update_one(filter={"_id": str(update.message.from_user.id)},
                         update={"$set": {f"chats.{chat_id}.info.age": int(update.message.text.strip())}})
        update.message.reply_text(
            "Понял :) Как давно ты в Анталии?"
        )
        return HOW_LONG_ANTALYA
    except ValueError:
        update.message.reply_text('Не понял тебя. Напиши числом, сколько тебе лет?')
        return AGE


def howlongantalya(update, context):
    user_id = str(update.message.from_user.id)
    chat_id = users.find_one({"_id": user_id})["now_introducing"]
    users.update_one(filter={"_id": str(update.message.from_user.id)},
                     update={"$set": {f"chats.{chat_id}.info.in_antalya": update.message.text}})
    update.message.reply_text('Хорошо! Кто ты по специальности?\n(разработчик С++, веб-дизайнер, ... ?')
    return SPECIALTY


def specialty(update, context):
    user_id = str(update.message.from_user.id)
    chat_id = users.find_one({"_id": user_id})["now_introducing"]
    users.update_one(filter={"_id": str(update.message.from_user.id)},
                     update={"$set": {f"chats.{chat_id}.info.specialty": update.message.text}})
    update.message.reply_text('И сколько лет ты уже в этой профессии?')
    return EXPERIENCE


def experience(update, context):
    try:
        user_id = str(update.message.from_user.id)
        chat_id = users.find_one({"_id": user_id})["now_introducing"]
        users.update_one(filter={"_id": str(update.message.from_user.id)},
                         update={"$set": {f"chats.{chat_id}.info.years_experience": int(update.message.text.strip())}})
        update.message.reply_text(
            "А в каких технологиях ты силён / сильна? (твой стек)"
        )
        return STACK
    except ValueError:
        update.message.reply_text('Не понял тебя. Напиши числом, сколько лет ты в профессии?')
        return EXPERIENCE


def stack(update, context):
    user_id = str(update.message.from_user.id)
    chat_id = users.find_one({"_id": user_id})["now_introducing"]
    users.update_one(filter={"_id": str(update.message.from_user.id)},
                     update={"$set": {f"chats.{chat_id}.info.stack": update.message.text}})
    update.message.reply_text('Ок! Чем занимался / занималась на последних проектах? (мин. 25 слов)')
    return RECENT_PROJECTS


def recent_projects(update, context):
    text = update.message.text
    if len(text.split()) < 25:
        update.message.reply_text('Слишком коротко! Пожалуйста, напиши больше, мне интересно :)')
        return RECENT_PROJECTS
    user_id = str(update.message.from_user.id)
    chat_id = users.find_one({"_id": user_id})["now_introducing"]
    users.update_one(filter={"_id": str(update.message.from_user.id)},
                     update={"$set": {f"chats.{chat_id}.info.recent_project": text}})
    update.message.reply_text('Чем интересуешься? Какие у тебя увлечения, хобби?')
    return HOBBY


def hobby(update, context):
    user_id = str(update.message.from_user.id)
    chat_id = users.find_one({"_id": user_id})["now_introducing"]
    users.update_one(filter={"_id": str(update.message.from_user.id)},
                     update={"$set": {f"chats.{chat_id}.info.hobby": update.message.text}})
    reply_keyboard = [['Да', 'Нет']]
    markup_key = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text('Ищешь партнёров по хобби?',
                              reply_markup=markup_key)
    return HOBBY_PARTNERS


def hobby_partners(update, context):
    user_id = str(update.message.from_user.id)
    chat_id = users.find_one({"_id": user_id})["now_introducing"]
    if update.message.text == 'Да':
        users.update_one(filter={"_id": str(update.message.from_user.id)},
                         update={"$set": {f"chats.{chat_id}.info.hobby_partners": 1}})
    else:
        users.update_one(filter={"_id": str(update.message.from_user.id)},
                         update={"$set": {f"chats.{chat_id}.info.hobby_partners": 0}})
    reply_keyboard = [['Да', 'Нет']]
    markup_key = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text('И последний вопрос. Ищешь работу?',
                              reply_markup=markup_key)
    return LOOKING_JOB


def looking_job(update, context):
    user_id = str(update.message.from_user.id)
    chat_id = users.find_one({"_id": user_id})["now_introducing"]
    if update.message.text == 'Да':
        users.update_one(filter={"_id": str(update.message.from_user.id)},
                         update={"$set": {f"chats.{chat_id}.info.looking_for_job": 1}})
    else:
        users.update_one(filter={"_id": str(update.message.from_user.id)},
                         update={"$set": {f"chats.{chat_id}.info.looking_for_job": 0}})

    update.message.reply_text('Спасибо, что познакомились!\nТеперь все про тебя знают больше, '
                              'и ты можешь писать в чатик :) Велкам!',
                              reply_markup=ReplyKeyboardRemove())

    introduce_user(chat_id, user_id)

    return ConversationHandler.END


def cancel(update, context):
    user = update.message.from_user
    logger.info("Пользователь %s отменил разговор.", user.first_name)

    update.message.reply_text(
        'Ну, как хочешь. Будет желание - пиши.',
        reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def help(update, context):
    """ /help command """
    bot.sendMessage(update.message.chat.id, "Прежде, чем писать в чат, где я админ (!),"
                                            " нужно ответить на несколько простых вопросов.\n"
                                            "Ответил? Отлично, теперь все знают, кто ты :)\n"
                                            "Не познакомились за день, или упорно писал в чат до знакомства? Бан 😊\n"
                                            "ВАЖНО: НЕ ЗАБУДЬ сделать меня администратором!\n"
                                            "Я живу здесь: https://github.com/Pythonimous/whois_bot")
