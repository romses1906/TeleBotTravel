from telegram_bot_calendar import DetailedTelegramCalendar
from loguru import logger
from typing import Any


def get_calendar(is_process: bool = False, callback_data: Any = None, **kwargs):
    """
    Функция для создания календаря

    :param is_process: bool
    :param callback_data: Any
    :param kwargs: передаются параметры для создания календаря
    :return: календарь  с поочередным выбором года, месяца, дня
    """
    try:
        if is_process:
            result, key, step = DetailedTelegramCalendar(calendar_id=kwargs['calendar_id'],
                                                         current_date=kwargs.get('current_date'),
                                                         min_date=kwargs['min_date'],
                                                         max_date=kwargs['max_date'],
                                                         locale=kwargs['locale']).process(callback_data.data)
            return result, key, step
        else:
            calendar, step = DetailedTelegramCalendar(calendar_id=kwargs['calendar_id'],
                                                      current_date=kwargs.get('current_date'),
                                                      min_date=kwargs['min_date'],
                                                      max_date=kwargs['max_date'],
                                                      locale=kwargs['locale']).build()
            return calendar, step
    except (KeyError, ValueError, LookupError, TypeError) as exc:
        logger.exception(exc)
