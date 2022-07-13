from config_data.config import DEFAULT_COMMANDS
from telebot.types import BotCommand


def set_default_commands(bot):
    bot.set_my_commands(
        [BotCommand(*i_command) for i_command in DEFAULT_COMMANDS]
    )
