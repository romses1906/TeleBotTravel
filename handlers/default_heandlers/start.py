from telebot.types import Message
from loader import bot
from loguru import logger


@bot.message_handler(commands=['start'])
def bot_start(message: Message) -> None:
    """
    Хэндлер команды 'start', выводит на экран приветственное сообщение

    :param message: Message
    :return: None
    """
    bot.reply_to(message,
                 f'Привет, {message.from_user.full_name}! Я Трэвэл Бот)\nЧтобы узнать мои команды напиши "/help"')
    logger.info(f"Пользователь {message.from_user.id} выбрал команду '/start'")
