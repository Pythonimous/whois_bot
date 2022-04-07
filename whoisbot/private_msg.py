from .config import bot


def start(update, context):
    """ /start command """
    bot.sendMessage(update.message.chat.id, "Привет! Просто добавь меня в чат, и я сделаю всё сам.\n"
                                            "ВАЖНО: НЕ ЗАБУДЬ сделать меня администратором 😉")


def help(update, context):
    """ /help command """
    bot.sendMessage(update.message.chat.id, "Я работаю просто.\n"
                                            "Каждый, кто заходит в МОЙ чат, должен представиться с #whois "
                                            "за 5 слов и более. У него три попытки. Не смог? Бан на сутки! 😊\n"
                                            "ВАЖНО: НЕ ЗАБУДЬ сделать меня администратором 😉\n"
                                            "Я живу здесь: https://github.com/Pythonimous/whois_bot")
