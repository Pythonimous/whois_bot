from whoisbot.config import bot, seen_users, user_info, logger
from whoisbot.utils import introduce_user
from telegram.ext import ConversationHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove

currently_introducing = {}


def start(update, context):
    """ /start command """
    user_id = update.message.from_user.id
    if user_id not in seen_users:
        bot.sendMessage(update.message.chat.id, "Привет! Просто добавь меня в чат, и я сделаю всё сам.\n"
                                                "ВАЖНО: НЕ ЗАБУДЬ сделать меня администратором 😉")
        return ConversationHandler.END
    else:
        bot.sendMessage(update.message.chat.id, f"Привет! Ты ещё не представился в чатах:\n"
                                                f"{'; '.join(seen_users[user_id])}.\n"
                                                f"В каком хочешь представиться?\n"
                                                f"Или /cancel, чтобы прекратить разговор.")
        return 0


def chat(update, context):
    user_id = update.message.from_user.id
    if update.message.text not in seen_users[user_id]:
        bot.sendMessage(update.message.chat.id, "Не знаю этот чат. Попробуй ещё раз!")
        return 0
    else:
        currently_introducing[user_id] = {"chat_id": seen_users[user_id][update.message.text],
                                          "info": {}}
        bot.sendMessage(update.message.chat.id, 'Хорошо! Как к тебе обращаться? '
                                                'Назови имя, или никнейм, если больше нравится.')
        return 1


def name(update, context):
    # определяем пользователя
    currently_introducing[update.message.from_user.id]["info"]["name"] = update.message.text

    update.message.reply_text(
        'Хорошо! Сколько тебе лет? (напиши число)',
        reply_markup=ReplyKeyboardRemove(),
    )
    return 2


def age(update, context):
    try:
        currently_introducing[update.message.from_user.id]["info"]['age'] = int(update.message.text.strip())
        update.message.reply_text(
            "Понял :) Как давно ты в Анталии?"
        )
        return 3
    except TypeError:
        update.message.reply_text('Не понял тебя. Напиши числом, сколько тебе лет?')
        return 2


def howlongantalya(update, context):
    currently_introducing[update.message.from_user.id]["info"]["in_antalya"] = update.message.text
    update.message.reply_text('Хорошо! Кто ты по специальности?\n(разработчик С++, веб-дизайнер, ... ?')
    return 4


def specialty(update, context):
    currently_introducing[update.message.from_user.id]["info"]["specialty"] = update.message.text
    update.message.reply_text('И сколько лет ты уже в этой профессии?')
    return 5


def experience(update, context):
    try:
        currently_introducing[update.message.from_user.id]["info"]['years_experience'] = int(update.message.text.strip())
        update.message.reply_text(
            "А в каких технологиях ты силён / сильна? (твой стек)"
        )
        return 6
    except TypeError:
        update.message.reply_text('Не понял тебя. Напиши числом, сколько лет ты в профессии?')
        return 5


def stack(update, context):
    currently_introducing[update.message.from_user.id]["info"]["stack"] = update.message.text
    update.message.reply_text('Ок! Чем занимался / занималась на последних проектах? (мин. 25 слов)')
    return 7


def recent_projects(update, context):
    text = update.message.text
    if len(text.split()) < 25:
        update.message.reply_text('Слишком коротко! Пожалуйста, напиши больше, мне интересно :)')
        return 7
    currently_introducing[update.message.from_user.id]["info"]["recent_project"] = text
    update.message.reply_text('Чем интересуешься? Какие у тебя увлечения, хобби?')
    return 8


def hobby(update, context):
    currently_introducing[update.message.from_user.id]["info"]["hobby"] = update.message.text
    reply_keyboard = [['Да', 'Нет']]
    markup_key = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text('Ищешь партнёров по хобби?',
                              reply_markup=markup_key)
    return 9


def looking_for_job(update, context):
    if update.message.text == 'Да':
        currently_introducing[update.message.from_user.id]["info"]["hobby_partners"] = 1
    else:
        currently_introducing[update.message.from_user.id]["info"]["hobby_partners"] = 0
    reply_keyboard = [['Да', 'Нет']]
    markup_key = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text('И последний вопрос. Ищешь работу?',
                              reply_markup=markup_key)
    return 10


def end_convo(update, context):
    if update.message.text == 'Да':
        currently_introducing[update.message.from_user.id]["info"]["looking_for_job"] = 1
    else:
        currently_introducing[update.message.from_user.id]["info"]["looking_for_job"] = 0
    user = update.message.from_user

    update.message.reply_text('Спасибо, что познакомились!\nТеперь все про тебя знают больше, '
                              'и ты можешь писать в чатик :) Велкам!')

    chat_id = currently_introducing[user.id]["chat_id"]

    currently_introducing[user.id]["info"]["username"] = update.message.from_user.username or update.message.from_user.first_name

    user_info[user.id][chat_id] = currently_introducing[user.id]["info"]
    del currently_introducing[user.id]

    introduce_user(chat_id, user.id)

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
