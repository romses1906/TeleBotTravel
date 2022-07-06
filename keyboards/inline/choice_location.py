import requests
import json
import re
from telebot import types
from telebot.types import Message, InlineKeyboardMarkup
from loader import bot
from handlers.work_with_api import request
from config_data import config
from typing import List, Dict, Optional, Match
from requests import Response


# возможно перенести в апи сити фаундинг

def city_founding(city: str) -> List[Dict[str, str]]:
    """
    Функция для запроса к API и поиска локаций в введенном пользователем городе

    :param city: город, выбранный пользователем для поиска отелей
    :return: список словарей с наименованиями локаций  и их id
    """
    url_locations_search: str = "https://hotels4.p.rapidapi.com/locations/v2/search"

    querystring_locations_search: Dict[str, str] = {"query": city, "locale": "ru_RU", "currency": "RUB"}

    response: Response = request.get_request(url=url_locations_search, headers=config.headers,
                                             params=querystring_locations_search)
    pattern: str = r'(?<="CITY_GROUP",).+?[\]]'
    find: Optional[Match[str]] = re.search(pattern, response.text)
    if find:
        suggestions: Dict = json.loads(f"{{{find[0]}}}")

        cities: List = list()
        for dest_id in suggestions['entities']:  # Обрабатываем результат
            clear_destination: str = re.sub('<([^<>]*)>', '', dest_id['caption'])
            cities.append({'city_name': clear_destination, 'destination_id': dest_id['destinationId']})

        return cities


def city_markup(user_city: str) -> InlineKeyboardMarkup:
    """
    Функция создания инлайн-кнопок для уточнения локации в выбранном городе

    :param user_city: город, выбранный пользователем для поиска отелей
    :return: инлайн-кнопки для выбора локации в указанном городе
    """
    cities: List[Dict[str, str]] = city_founding(city=user_city)
    # Функция "city_founding" уже возвращает список словарей с нужным именем и id
    destinations: InlineKeyboardMarkup = types.InlineKeyboardMarkup()
    for city in cities:
        destinations.add(types.InlineKeyboardButton(text=city['city_name'],
                                                    callback_data=f'{city["destination_id"]}'))
    return destinations


def city(message: Message) -> None:
    """
    Функция вывода на экран inline-кнопок для уточнения локации в выбранном городе

    :param message: Message
    :return: None
    """
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['city']: str = message.text
        bot.send_message(message.from_user.id, 'Уточните, пожалуйста:',
                         reply_markup=city_markup(user_city=data['city']))  # Отправляем кнопки с вариантами
