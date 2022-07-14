from . import request
from requests import Response
import json
from json import JSONDecodeError
from loader import bot
from config_data import config
from typing import List, Dict, Any
from telebot.types import InputMediaPhoto
from loguru import logger

logger.add('debug.log', level='DEBUG', format="{time} {level} {message}", rotation="08:00",
           compression="zip")


def hotels(user: Any, chat: Any) -> None:
    """
    Функция для запроса к API и получения необходимых данных об отелях

    :param user: Any
    :param chat: Any
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

        if data['command'] == '/lowprice':
            try:
                response: Response = request.get_request(url=url, headers=config.headers, params=querystring)
                hotels_dict: Dict = json.loads(response.text)
                hotels_lst: List[Dict] = hotels_dict['data']['body']['searchResults']['results']  # список со словарями
                result_hotels_lst: List = []

                for i_hotel in hotels_lst:

                    if i_hotel['name'] and i_hotel['id'] and i_hotel['address']['streetAddress'] and \
                            i_hotel['landmarks'][0]['label'] and i_hotel['landmarks'][1]['label'] and \
                            i_hotel['ratePlan']['price']['exactCurrent']:  # проверяю, есть ли такие параметры
                        result_hotels_lst.append(i_hotel)
            except (KeyError, ValueError, LookupError, TypeError, IndexError, JSONDecodeError) as exc:
                logger.exception(exc)

            if len(result_hotels_lst) == 0:
                bot.send_message(user, 'К сожалению, отелей, удовлетворяющих условиям Вашего запроса, не найдено. '
                                       'Попробуйте изменить условия поиска, приносим свои извинения.')
            elif len(result_hotels_lst) < int(data['count_hotels']):
                bot.send_message(user,
                                 f'К сожалению, удалось найти только {len(result_hotels_lst)} отеля, '
                                 f'удовлетворяющих условиям Вашего запроса. '
                                 'Попробуйте изменить условия поиска, приносим свои извинения.')

            for i_hot in result_hotels_lst[:int(data['count_hotels'])]:
                send_info_hotel(user, chat, hotel=i_hot)

        elif data['command'] == '/highprice':
            try:
                response: Response = request.get_request(url=url, headers=config.headers, params=querystring)

                hotels_dict: Dict = json.loads(response.text)
                hotels_lst: List[Dict] = hotels_dict['data']['body']['searchResults']['results']
                result_hotels_lst: List = []

                for i_hotel in hotels_lst:

                    if i_hotel['name'] and i_hotel['id'] and i_hotel['address']['streetAddress'] and \
                            i_hotel['landmarks'][0]['label'] and i_hotel['landmarks'][1]['label'] and \
                            i_hotel['ratePlan']['price']['exactCurrent']:
                        result_hotels_lst.append(i_hotel)

            except (KeyError, ValueError, LookupError, TypeError, IndexError, JSONDecodeError) as exc:
                logger.exception(exc)

            if len(result_hotels_lst) == 0:
                bot.send_message(user, 'К сожалению, отелей, удовлетворяющих условиям Вашего запроса, не найдено. '
                                       'Попробуйте изменить условия поиска, приносим свои извинения.')
            elif len(result_hotels_lst) < int(data['count_hotels']):
                bot.send_message(user,
                                 f'К сожалению, удалось найти только {len(result_hotels_lst)} отеля, '
                                 f'удовлетворяющих условиям Вашего запроса. '
                                 'Попробуйте изменить условия поиска, приносим свои извинения.')

            for i_hot in result_hotels_lst[:int(data['count_hotels'])]:
                send_info_hotel(user, chat, hotel=i_hot)

        elif data['command'] == '/bestdeal':
            try:
                response: Response = request.get_request(url=url, headers=config.headers, params=querystring)
                hotels_dict: Dict = json.loads(response.text)
                hotels_lst: List[Dict] = hotels_dict['data']['body']['searchResults']['results']
                result_hotels_lst: List = []

                for i_hotel in hotels_lst:

                    if i_hotel['name'] and i_hotel['id'] and i_hotel['address']['streetAddress'] and \
                            i_hotel['landmarks'][0]['label'] and i_hotel['landmarks'][1]['label'] and \
                            i_hotel['ratePlan']['price']['exactCurrent'] and float(i_hotel['landmarks'][0]['distance'][
                                                                                   :3].replace(',', '.')) <= float(data[
                                                                                                                       'distance_range']):
                        result_hotels_lst.append(i_hotel)
            except (KeyError, ValueError, LookupError, TypeError, IndexError, JSONDecodeError) as exc:
                logger.exception(exc)
            result_hotels_lst_sorted: List[Dict] = sorted(result_hotels_lst,
                                                          key=lambda elem: elem['ratePlan']['price']['exactCurrent'])

            if len(result_hotels_lst_sorted) == 0:
                bot.send_message(user, 'К сожалению, отелей, удовлетворяющих условиям Вашего запроса, не найдено. '
                                       'Попробуйте изменить условия поиска, приносим свои извинения.')
            elif len(result_hotels_lst_sorted) < int(data['count_hotels']):
                bot.send_message(user,
                                 f'К сожалению, удалось найти только {len(result_hotels_lst_sorted)} отеля, '
                                 f'удовлетворяющих условиям Вашего запроса. '
                                 'Попробуйте изменить условия поиска, приносим свои извинения.')

            for i_hot in result_hotels_lst_sorted[:int(data['count_hotels'])]:
                send_info_hotel(user, chat, hotel=i_hot)


def photo(user: Any, chat: Any, id_hotel: str):
    """
    Функция для запроса к API и вывода фотографий отелей на экран

    :param user: Any
    :param chat: Any
    :param id_hotel: str
    :return: None
    """
    url: str = "https://hotels4.p.rapidapi.com/properties/get-hotel-photos"
    try:
        with bot.retrieve_data(user, chat) as data:
            querystring: Dict[str, str] = {"id": id_hotel}

            response: Response = request.get_request(url=url, headers=config.headers, params=querystring)
            photos: Dict = json.loads(response.text)
            photos_lst: List = photos['hotelImages'][:int(data['count_photo'])]
            photo_media_lst = []
            for i_photo in photos_lst:
                url_photo: str = i_photo['baseUrl'].replace('_{size}', '')
                photo_media_lst.append(url_photo)

            return photo_media_lst
    except (TypeError, JSONDecodeError) as exc:
        logger.exception(exc)


def send_info_hotel(user: Any, chat: Any, hotel: Dict) -> None:
    """
    Функция вывода на экран необходимой информации об отеле

    :param user: Any
    :param chat: Any
    :param hotel: Dict
    :return: None
    """
    try:
        with bot.retrieve_data(user, chat) as data:
            name: str = hotel['name']
            hotel_id = data['hotel_id'] = hotel['id']
            adress: str = hotel['address']['streetAddress']
            name_label_1: str = hotel['landmarks'][0]['label']
            distance_from_label_1: str = hotel['landmarks'][0]['distance']
            name_label_2: str = hotel['landmarks'][1]['label']
            distance_from_label_2: str = hotel['landmarks'][1]['distance']
            price: float = hotel['ratePlan']['price']['exactCurrent']
            rest_days: int = (data['date_departure'] - data['date_arrival']).days
            full_price: float = round(price * rest_days, 2)
            find_info = f'Название отеля: {name}\nСайт отеля: https://www.hotels.com/ho{hotel_id}\n' \
                        f'Адрес отеля: {adress}\n' \
                        f'Расстояние от отеля до "{name_label_1}": {distance_from_label_1}\n' \
                        f'Расстояние от отеля до "{name_label_2}": {distance_from_label_2}\n' \
                        f'Стоимость проживания за 1 сутки: {price} RUB\n' \
                        f'Стоимость проживания за {rest_days} суток: {full_price} RUB'

            media_lst = photo(user=user, chat=chat, id_hotel=hotel_id)

            media = [InputMediaPhoto(media_lst[pic], find_info) if pic == len(media_lst) - 1 else InputMediaPhoto(
                media_lst[pic]) for pic in range(len(media_lst))]

            bot.send_media_group(chat, media)

    except (KeyError, ValueError, LookupError, TypeError, IndexError) as exc:
        logger.exception(exc)
