from telebot.types import Message
from loader import bot
from loguru import logger


@bot.message_handler(commands=['help'])
def bot_help(message: Message) -> None:
    """
    Хэндлер команды 'help', выводит на экран список команд телеграм-бота

    :param message: Message - сообщение от пользователя с командой 'help'
    :return: None
    """
    text = ("Список команд: ",
            "/start - Начать диалог",
            "/help - Помощь по командам бота",
            "/lowprice - Вывод самых дешевых отелей в городе",
            "/highprice - Вывод самых дорогих отелей в городе",
            "/bestdeal - Вывод отелей, наиболее подходящих по цене и расположению от центра",
            "/history - Вывод истории поиска отелей",
            )
    bot.reply_to(message, '\n'.join(text))
    logger.info(f"Пользователь {message.from_user.id} выбрал команду '/help'")
