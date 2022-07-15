from telebot.types import Message

from loader import bot


@bot.message_handler(commands=['help'])
def bot_help(message: Message) -> None:
    text = ("Список команд: ",
            "/start - Начать диалог",
            "/help - Помощь по командам бота",
            "/lowprice - Вывод самых дешевых отелей в городе",
            "/highprice - Вывод самых дорогих отелей в городе",
            "/bestdeal - Вывод отелей, наиболее подходящих по цене и расположению от центра",
            "/history - Вывод истории поиска отелей",
            )
    bot.reply_to(message, '\n'.join(text))

# TODO дописать докстринги
