from telebot.types import Message
from loader import bot
from loguru import logger


@bot.message_handler(state=None)
def bot_echo(message: Message) -> None:
    """
    Эхо-хендлер, куда поступают текстовые сообщения без указанного состояния

    :param message: Message
    :return: None
    """

    bot.reply_to(message, f'Эхо без состояния или фильтра.\nСообщение: {message.text}')
    logger.info(f"Для пользователя {message.from_user.id} сработал эхо-хендлер. Сообщение пользователя: {message.text}")
