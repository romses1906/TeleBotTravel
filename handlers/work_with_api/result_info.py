from . import request
from requests import Response
import json
from telebot import apihelper
from json import JSONDecodeError
from loader import bot
from config_data import config
from typing import List, Dict, Any
from telebot.types import InputMediaPhoto
from loguru import logger
from database import models
from database import dbworker


def debug_only(record: Dict) -> bool:  # не уверен по поводу аннотации
    """
    Функция создания фильтра логов для файла debug.log.

    :param record: Dict
    :return: bool
    """

    return record["level"].name == "ERROR"


logger.add('debug.log', format="{time} {level} {message}", rotation="08:00",
           compression="zip", filter=debug_only)


def hotels(user: Any, chat: Any) -> None:
    """
    Функция для запроса к API и получения необходимых данных об отелях
    в зависимости от изначальной команды пользователя

    :param user: Any - id пользователя
    :param chat: Any - id чата
    :return: None
    """
    url: str = "https://hotels4.p.rapidapi.com/properties/list"

    with bot.retrieve_data(user, chat) as data:
        priceMin: str = ''
        priceMax: str = ''
        landmarkIds: str = ''
        if data['command'] == '/lowprice':
            sortOrder: str = 'PRICE'

        elif data['command'] == '/highprice':
            sortOrder: str = 'PRICE_HIGHEST_FIRST'

        elif data['command'] == '/bestdeal':
            sortOrder: str = 'DISTANCE_FROM_LANDMARK'
            landmarkIds: str = 'Центр города'
            priceMin: str = data['min_price']
            priceMax: str = data['max_price']

        querystring: Dict[str, str] = {"destinationId": data['location_id'], "pageNumber": "1", "pageSize": "25",
                                       "checkIn": data['date_arrival'],
                                       "checkOut": data['date_departure'], "adults1": "1", "priceMin": priceMin,
                                       "priceMax": priceMax,
                                       "sortOrder": sortOrder, "locale": "ru_RU",
                                       "currency": "RUB", "landmarkIds": landmarkIds}

        if data['command'] == '/lowprice' or data['command'] == '/highprice':
            hotels_low_high(user=user, chat=chat, url=url, querystring=querystring)

        elif data['command'] == '/bestdeal':
            try:
                response: Response = request.get_request(url=url, headers=config.headers, params=querystring)
                data_hotels: Dict = json.loads(response.text)
                hotels_info: List[Dict] = data_hotels['data']['body']['searchResults']['results']
                result_hotels: List = []

                for hotel in hotels_info:

                    if hotel['name'] and hotel['id'] and hotel['address']['streetAddress'] and hotel['landmarks'][0][
                        'label'] and hotel['landmarks'][1]['label'] and hotel['ratePlan']['price'][
                        'exactCurrent'] and float(hotel['landmarks'][0]['distance'][
                                                  :3].replace(',', '.')) <= float(data['distance_range']):
                        result_hotels.append(hotel)
            except (KeyError, ValueError, LookupError, TypeError, IndexError, JSONDecodeError) as exc:
                logger.exception(exc)
            result_hotels_sorted: List[Dict] = sorted(result_hotels,
                                                      key=lambda elem: elem['ratePlan']['price']['exactCurrent'])

            if len(result_hotels_sorted) == 0:
                bot.send_message(user, 'К сожалению, отелей, удовлетворяющих условиям Вашего запроса, не найдено. '
                                       'Попробуйте изменить условия поиска, приносим свои извинения.')
                logger.info('К сожалению, отелей, удовлетворяющих условиям Вашего запроса, не найдено. '
                            'Попробуйте изменить условия поиска, приносим свои извинения.')
            elif len(result_hotels_sorted) < int(data['count_hotels']):
                bot.send_message(user,
                                 f'К сожалению, удалось найти только {len(result_hotels_sorted)} отеля, '
                                 f'удовлетворяющих условиям Вашего запроса. '
                                 'Попробуйте изменить условия поиска, приносим свои извинения.')
                logger.info(f'К сожалению, удалось найти только {len(result_hotels_sorted)} отеля, '
                            f'удовлетворяющих условиям Вашего запроса. '
                            'Попробуйте изменить условия поиска, приносим свои извинения.')
            if result_hotels_sorted:
                logger.info(f"Результат поиска отелей для пользователя {user}:\n")
            for hotel in result_hotels_sorted[:int(data['count_hotels'])]:
                send_info_hotel(user, chat, hotel=hotel)
                dbworker.save_db(user, chat, hotel=hotel)


def hotels_low_high(user: Any, chat: Any, url: str, querystring: Dict[str, str]) -> None:
    """
    Функция для запроса к API и получения необходимых данных об отелях
    при команде пользователя 'lowprice' или 'highprice'

    :param user: Any - id пользователя
    :param chat: Any - id чата
    :param url: str - адрес сайта для поиска отелей
    :param querystring: Dict[str, str] - необходимые параметры для поиска отелей
    :return: None
    """
    with bot.retrieve_data(user, chat) as data:
        try:
            response: Response = request.get_request(url=url, headers=config.headers, params=querystring)
            data_hotels: Dict = json.loads(response.text)
            hotels_info: List[Dict] = data_hotels['data']['body']['searchResults']['results']  # список со словарями
            result_hotels: List = []

            for hotel in hotels_info:

                if hotel['name'] and hotel['id'] and hotel['address']['streetAddress'] and hotel['landmarks'][0][
                    'label'] and hotel['landmarks'][1]['label'] and hotel['ratePlan']['price']['exactCurrent']:
                    result_hotels.append(hotel)

        except (KeyError, ValueError, LookupError, TypeError, IndexError, JSONDecodeError) as exc:
            logger.exception(exc)

        if len(result_hotels) == 0:
            bot.send_message(user, 'К сожалению, отелей, удовлетворяющих условиям Вашего запроса, не найдено. '
                                   'Попробуйте изменить условия поиска, приносим свои извинения.')
            logger.info('К сожалению, отелей, удовлетворяющих условиям Вашего запроса, не найдено. '
                        'Попробуйте изменить условия поиска, приносим свои извинения.')
        elif len(result_hotels) < int(data['count_hotels']):
            bot.send_message(user,
                             f'К сожалению, удалось найти только {len(result_hotels)} отеля, '
                             f'удовлетворяющих условиям Вашего запроса. '
                             'Попробуйте изменить условия поиска, приносим свои извинения.')
            logger.info(f'К сожалению, удалось найти только {len(result_hotels)} отеля, '
                        f'удовлетворяющих условиям Вашего запроса. '
                        'Попробуйте изменить условия поиска, приносим свои извинения.')
        if result_hotels:
            logger.info(f"Результат поиска отелей для пользователя {user}:\n")
        for hotel in result_hotels[:int(data['count_hotels'])]:
            send_info_hotel(user, chat, hotel=hotel)
            dbworker.save_db(user, chat, hotel=hotel)


def photo(user: Any, chat: Any, id_hotel: str) -> List[str]:
    """
    Функция для запроса к API и вывода фотографий отелей на экран

    :param user: Any - id пользователя
    :param chat: Any - id чата
    :param id_hotel: str - id отеля
    :return: None
    """
    url: str = "https://hotels4.p.rapidapi.com/properties/get-hotel-photos"
    try:
        with bot.retrieve_data(user, chat) as data:
            querystring: Dict[str, str] = {"id": id_hotel}

            response: Response = request.get_request(url=url, headers=config.headers, params=querystring)
            photos: Dict = json.loads(response.text)
            photos_info: List = photos['hotelImages'][:int(data['count_photo'])]
            photo_media: List = []
            for picture in photos_info:
                url_photo: str = picture['baseUrl'].replace('_{size}', '')
                photo_media.append(url_photo)

            return photo_media
    except (TypeError, AttributeError, JSONDecodeError) as exc:
        logger.exception(exc)


def send_info_hotel(user: Any, chat: Any, hotel: Dict) -> None:
    """
    Функция вывода на экран необходимой информации об отеле

    :param user: Any - id пользователя
    :param chat: Any - id чата
    :param hotel: Dict - словарь с данными об отеле
    :return: None
    """
    try:
        with bot.retrieve_data(user, chat) as data:
            hotel_name: str = hotel['name']
            hotel_id = data['hotel_id'] = hotel['id']
            address: str = hotel['address']['streetAddress']
            rating: str = hotel['starRating']
            name_label_1: str = hotel['landmarks'][0]['label']
            distance_from_label_1: str = hotel['landmarks'][0]['distance']
            name_label_2: str = hotel['landmarks'][1]['label']
            distance_from_label_2: str = hotel['landmarks'][1]['distance']
            price: float = hotel['ratePlan']['price']['exactCurrent']
            rest_days: int = (data['date_departure'] - data['date_arrival']).days
            full_price: float = round(price * rest_days, 2)
            find_info = (f'Название отеля: {hotel_name}\nСайт отеля: https://www.hotels.com/ho{hotel_id}\n'
                         f'Адрес отеля: {address}\n'
                         f'Рейтинг отеля (количество звезд): {rating}\n'
                         f'Расстояние от отеля до "{name_label_1}": {distance_from_label_1}\n'
                         f'Расстояние от отеля до "{name_label_2}": {distance_from_label_2}\n'
                         f'Стоимость проживания за 1 сутки: {price} RUB\n'
                         f'Стоимость проживания за {rest_days} суток: {full_price} RUB')

            logger.info(f"Отель по результатам поиска для пользователя {user}: {find_info}\n")

            find_media: List[str] = photo(user=user, chat=chat, id_hotel=hotel_id)

            media_group: List[InputMediaPhoto] = [InputMediaPhoto(find_media[num_photo], find_info) if num_photo == len(
                find_media) - 1 else InputMediaPhoto(
                find_media[num_photo]) for num_photo in range(len(find_media))]
            if data['count_photo'] == 0:
                bot.send_message(user, find_info)

            else:
                bot.send_media_group(chat, media_group)
            models.History.create_table()

    except (KeyError, ValueError, LookupError, TypeError, IndexError, apihelper.ApiTelegramException) as exc:
        logger.exception(exc)
