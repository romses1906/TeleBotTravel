from database import models
from loader import bot
from typing import Dict, List, Any
from loguru import logger
from telebot.types import Message
import peewee


def save_db(user: Any, chat: Any, hotel: Dict) -> None:
    """
    Функция для записи данных в таблицу базы данных

    :param user: Any
    :param chat: Any
    :param hotel: Dict
    :return: None
    """
    try:
        with bot.retrieve_data(user, chat) as data:
            location: str = data['location']
            hotel_name: str = hotel['name']
            hotel_id = data['hotel_id'] = hotel['id']
            address: str = hotel['address']['streetAddress']
            name_label_1: str = hotel['landmarks'][0]['label']
            distance_from_label_1: str = hotel['landmarks'][0]['distance']
            name_label_2: str = hotel['landmarks'][1]['label']
            distance_from_label_2: str = hotel['landmarks'][1]['distance']
            price: float = hotel['ratePlan']['price']['exactCurrent']
            rest_days: int = (data['date_departure'] - data['date_arrival']).days
            full_price: float = round(price * rest_days, 2)
            command = data['command']
            hist = models.History.create(uid=user, location=location, hotel_name=hotel_name, hotel_id=hotel_id,
                                         site=f'https://www.hotels.com/ho{hotel_id}',
                                         address=address, name_label_1=name_label_1,
                                         distance_from_label_1=distance_from_label_1,
                                         name_label_2=name_label_2, distance_from_label_2=distance_from_label_2,
                                         price=price,
                                         rest_days=rest_days, full_price=full_price, command=command)
            hist.save()

    except (KeyError, ValueError, LookupError, TypeError, IndexError, peewee.OperationalError) as exc:
        logger.exception(exc)


def get_history(message: Message) -> None:
    """
    Функция для получения и вывода на экран данных об истории поиска отелей конкретного пользователя
    из таблицы базы данных history

    :param message: Message
    :return: None
    """
    query: Any = models.History.select().where((models.History.uid == message.from_user.id)).order_by(
        models.History.date.desc())
    users_id: List = []
    try:
        for user_id in models.History.select(models.History.uid):
            users_id.append(user_id.uid)

        if str(message.from_user.id) not in users_id:
            bot.send_message(message.from_user.id, 'На данный момент, для данного аккаунта история поиска отсутствует')
        else:
            bot.send_message(message.from_user.id, 'Вывожу Вашу историю поиска отелей: ')

            for data in query:
                bot.send_message(message.from_user.id, f'Команда пользователя: {data.command}\n'
                                                       f'Дата запроса: {data.date}\n'
                                                       f'Локация для поиска: {data.location}\n'
                                                       f'Название отеля: {data.hotel_name}\n'
                                                       f'Сайт отеля: https://www.hotels.com/ho{data.hotel_id}\n'
                                                       f'Адрес отеля: {data.address}\n'
                                                       f'Расстояние от отеля до "{data.name_label_1}": '
                                                       f'{data.distance_from_label_1}\n'
                                                       f'Расстояние от отеля до "{data.name_label_2}": '
                                                       f'{data.distance_from_label_2}\n'
                                                       f'Стоимость проживания за 1 сутки: {data.price} RUB\n'
                                                       f'Стоимость проживания за {data.rest_days} суток: '
                                                       f'{data.full_price} RUB')
    except (KeyError, ValueError, LookupError, TypeError, IndexError, peewee.OperationalError) as exc:
        logger.exception(exc)
        bot.send_message(message.from_user.id, 'На данный момент, для данного аккаунта история поиска отсутствует')
