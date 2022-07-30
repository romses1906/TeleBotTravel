from loader import bot
from states.contact_information import UserInfoState
from telebot import types
from telebot.types import Message, InlineKeyboardMarkup
from telegram_bot_calendar import DetailedTelegramCalendar
from datetime import date, timedelta
from keyboards import inline
from keyboards.inline import choice_location
from handlers.work_with_api import result_info
from typing import Dict, Any
from database import dbworker
from loguru import logger


def info_only(record: Dict) -> bool:  # не уверен по поводу аннотации
    """
    Функция создания фильтра логов для файла info.log.

    :param record: dict
    :return: bool
    """

    return record["level"].name == "INFO"


logger.add('info.log', format="{time} {level} {message}", rotation="08:00",
           compression="zip", filter=info_only)


@bot.message_handler(commands=['lowprice', 'highprice', 'bestdeal'])
def survey(message: Message) -> None:
    """
    Хэндлер команд 'lowprice', 'highprice', 'bestdeal',
    начинает запрашивать параметры от пользователя, присваивает состояние 'name'

    :param message: Message
    :return: None
    """
    bot.delete_state(message.from_user.id, message.chat.id)
    bot.set_state(message.from_user.id, UserInfoState.name, message.chat.id)
    bot.send_message(message.from_user.id, 'Как я могу к Вам обращаться?')
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['command'] = message.text
        logger.info(f"Пользователь {message.from_user.id} выбрал команду {data['command']}")


@bot.message_handler(commands=['history'])
def history(message: Message) -> None:
    """
    Хэндлер команды 'history', при вводе пользователем данной команды происходит
    вызов функции dbworker.get_history(message)

    :param message: Message
    :return: None
    """
    logger.info(f"Пользователь {message.from_user.id} выбрал команду '/history'")
    dbworker.get_history(message)


@bot.message_handler(state=UserInfoState.name)
def get_name(message: Message) -> None:
    """
    Хэндлер состояния 'name', запрашивает у пользователя город для поиска отелей,
    далее происходит уточнение локации в городе

    :param message: Message
    :return: None
    """
    if message.text.isalpha():
        bot.send_message(message.from_user.id,
                         'Спасибо, записал. Теперь введите город, в котором будет производиться поиск отелей')
        bot.set_state(message.from_user.id, UserInfoState.city, message.chat.id)
        bot.register_next_step_handler(message, choice_location.user_location)
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['name'] = message.text
            logger.info(f"Имя пользователя {message.from_user.id}: {data['name']}")

    else:
        bot.send_message(message.from_user.id, 'Имя может содержать только буквы')


ALL_STEPS: Dict[str, str] = {'y': 'год', 'm': 'месяц', 'd': 'день'}


@bot.callback_query_handler(func=lambda call: call.data.isdigit())
def get_location(call: types.CallbackQuery) -> None:
    """
    Обработчик inline-кнопок с выбором локации в городе,
    далее происходит уточнение даты заезда в отель

    :param call: CallbackQuery
    :return: None
    """
    bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id)
    bot.send_message(call.from_user.id,
                     'Спасибо, записал. Выберите дату заезда в отель')

    today: date = date.today()
    calendar, step = inline.calendar.get_calendar(calendar_id=1, current_date=today,
                                                  min_date=today, max_date=today + timedelta(days=365), locale='ru')

    bot.send_message(call.message.chat.id,
                     f"Выберите {ALL_STEPS[step]}",
                     reply_markup=calendar)

    with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
        locations: Any = call.message.json['reply_markup']['inline_keyboard']

        for location in locations:
            if call.data == location[0]['callback_data']:
                data['location']: str = location[0]['text']
                data['location_id']: str = call.data
                logger.info(f"Пользователь {call.from_user.id} выбрал локацию {data['location']}")

    bot.answer_callback_query(callback_query_id=call.id)


@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=1))
def handle_arrival_date(call: types.CallbackQuery) -> None:
    """
    Обработчик кнопок для выбора даты заезда, фиксирует дату заезда,
    далее происходит уточнение даты выезда из отеля

    :param call: CallbackQuery
    :return: None
    """
    today: date = date.today()
    result, key, step = inline.calendar.get_calendar(calendar_id=1, current_date=today,
                                                     min_date=today, max_date=today + timedelta(days=365), locale='ru',
                                                     is_process=True,
                                                     callback_data=call)
    if not result and key:
        bot.edit_message_text(f"Выберите {ALL_STEPS[step]}",
                              call.message.chat.id,
                              call.message.message_id,
                              reply_markup=key)
    elif result:
        with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
            data['date_arrival'] = result
            logger.info(f"Пользователь {call.from_user.id} выбрал дату заезда в отель: {data['date_arrival']}")

        bot.edit_message_text(f"Дата заезда: {result}",
                              call.message.chat.id,
                              call.message.message_id)

        bot.send_message(call.from_user.id,
                         'Спасибо, записал. Выберите дату выезда из отеля')
        calendar, step = inline.calendar.get_calendar(calendar_id=2, current_date=today,
                                                      min_date=result + timedelta(days=1),
                                                      max_date=result + timedelta(days=365), locale='ru')
        bot.send_message(call.message.chat.id,
                         f"Выберите {ALL_STEPS[step]}",
                         reply_markup=calendar)
        bot.set_state(call.from_user.id, UserInfoState.date_departure, call.message.chat.id)


@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=2))
def handle_departure_date(call: types.CallbackQuery) -> None:
    """
    Обработчик кнопок для выбора даты выезда, фиксирует дату выезда,
    далее происходит разветвление, в зависимости от изначально выбранной пользователем команды:
    'lowprice', 'highprice', 'bestdeal'. В случае выбора команды 'lowprice' или 'highprice'
    запрашивается количество отелей для вывода на экран, присваивается состояние 'count_hotels',
    в случае выбора команды 'bestdeal' запрашивается минимальная цена за 1 сутки проживания, присваивается состояние
    'min_price'

    :param call: CallbackQuery
    :return: None
    """
    today: date = date.today()
    with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
        result, key, step = inline.calendar.get_calendar(calendar_id=2, current_date=today,
                                                         min_date=data['date_arrival'] + timedelta(days=1),
                                                         max_date=data['date_arrival'] + timedelta(days=365),
                                                         locale='ru',
                                                         is_process=True, callback_data=call)

    if not result and key:
        bot.edit_message_text(f"Выберите {ALL_STEPS[step]}",
                              call.message.chat.id,
                              call.message.message_id,
                              reply_markup=key)
    elif result:
        with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
            data['date_departure'] = result
            logger.info(f"Пользователь {call.from_user.id} выбрал дату выезда из отеля: {data['date_departure']}")
        bot.edit_message_text(f"Дата выезда: {result}",
                              call.message.chat.id,
                              call.message.message_id)
        if data['command'] == '/bestdeal':
            bot.send_message(call.from_user.id,
                             'Введите диапазон цен для поиска подходящих отелей. Введите минимальную цену (руб)')
            bot.set_state(call.from_user.id, UserInfoState.min_price, call.message.chat.id)
        elif data['command'] == '/lowprice' or data['command'] == '/highprice':
            bot.send_message(call.from_user.id,
                             'Введите количество отелей, которое необходимо вывести в результате, но не более 5')
            bot.set_state(call.from_user.id, UserInfoState.count_hotels, call.message.chat.id)


# для bestdeal
@bot.message_handler(state=UserInfoState.min_price)
def get_min_price(message: Message) -> None:
    """
    Хэндлер состояния 'min_price', фиксирует минимальную цену проживания,
    запрашивает максимальную цену за 1 сутки проживания, присваивает состояние 'max_price'

    :param message: Message
    :return: None
    """
    if message.text.isdigit() and 0 < int(message.text):
        bot.send_message(message.from_user.id,
                         'Спасибо, записал. Введите максимальную цену (руб)')
        bot.set_state(message.from_user.id, UserInfoState.max_price, message.chat.id)

        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['min_price'] = message.text
            logger.info(f"Пользователь {message.from_user.id} задал минимальную цену за проживание за 1 сутки: "
                        f"{data['min_price']} RUB")

    else:
        bot.send_message(message.from_user.id,
                         'Введите пожалуйста целое неотрицательное число')


# для bestdeal
@bot.message_handler(state=UserInfoState.max_price)
def get_max_price(message: Message) -> None:
    """
    Хэндлер состояния 'max_price', фиксирует максимальную цену за 1 сутки проживания,
    запрашивает максимальную удаленность искомых отелей от центра города, присваивает состояние 'distance_range'

    :param message: Message
    :return: None
    """
    if message.text.isdigit() and 0 < int(message.text):
        bot.send_message(message.from_user.id,
                         'Спасибо, записал. Введите максимальное расстояние отелей от центра города для поиска (км)')
        bot.set_state(message.from_user.id, UserInfoState.distance_range, message.chat.id)

        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['max_price'] = message.text
            logger.info(f"Пользователь {message.from_user.id} задал максимальную цену за проживание за 1 сутки: "
                        f"{data['max_price']} RUB")

    else:
        bot.send_message(message.from_user.id,
                         'Введите пожалуйста целое неотрицательное число')


@bot.message_handler(state=UserInfoState.distance_range)
def get_distance_range(message: Message) -> None:
    """
    Хэндлер состояния 'distance_range', фиксирует максимальное расстояние от центра города,
    запрашивает количество выводимых на экран отелей, присваивает состояние 'count_hotels'

    :param message: Message
    :return: None
    """
    if message.text.isdigit() and 0 < int(message.text):
        bot.send_message(message.from_user.id,
                         'Спасибо, записал. Введите количество отелей, которое необходимо вывести в результате, '
                         'но не более 5')
        bot.set_state(message.from_user.id, UserInfoState.count_hotels, message.chat.id)

        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['distance_range'] = message.text
            logger.info(f"Пользователь {message.from_user.id} задал максимальной расстояние от центра города: "
                        f"{data['min_price']} км")

    else:
        bot.send_message(message.from_user.id,
                         'Введите пожалуйста целое неотрицательное число')


@bot.message_handler(state=UserInfoState.count_hotels)
def get_count_hotels(message: Message) -> None:
    """
    Хэндлер состояния 'count_hotels', фиксирует количество выводимых на экран отелей в результате поиска,
    запрашивает о необходимости вывода фото отелей на экран, присваивает состояние 'photo'

    :param message: Message
    :return: None
    """
    if message.text.isdigit() and 0 < int(message.text) <= 5:
        markup: InlineKeyboardMarkup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton('Да', callback_data='photo_please'))
        markup.add(types.InlineKeyboardButton('Нет', callback_data='no_photo'))
        bot.send_message(message.chat.id, 'Спасибо, записал. Необходимо ли вывести фотографии найденных отелей?',
                         reply_markup=markup)
        bot.set_state(message.from_user.id, UserInfoState.photo, message.chat.id)

        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['count_hotels'] = message.text
            logger.info(f"Пользователь {message.from_user.id} задал количество выводимых на экран отелей: "
                        f"{data['count_hotels']}")

    else:
        bot.send_message(message.from_user.id, 'Количество искомых отелей необходимо ввести числом от 1 до 5')


@bot.callback_query_handler(func=lambda call: True)
def get_photo(call: types.CallbackQuery) -> None:
    """
    Обработчик кнопок для выбора о выводе фото на экран, если нажата кнопка "да",
    запрашивает количество фото для вывода на экран и присваивает состояние 'count_photo',
    если нет, присваивает состояние 'final_info'

    :param call: CallbackQuery
    :return: None
    """
    bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id)
    if call.data == 'photo_please':
        bot.send_message(call.from_user.id,
                         'Спасибо, записал. Введите количество необходимых фото для каждого найденного отеля, '
                         'но не более 10')
        bot.set_state(call.from_user.id, UserInfoState.count_photo, call.message.chat.id)

        with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
            data['photo'] = call.data
            logger.info(f"Пользователь {call.from_user.id} выбрал вариант с небоходимостью вывода фото отелей на экран")

    elif call.data == 'no_photo':
        bot.send_message(call.from_user.id, 'Спасибо, записал, фото не нужны')
        bot.set_state(call.from_user.id, UserInfoState.final_information, call.message.chat.id)
        with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
            data['count_photo'] = 0
            logger.info(f"Пользователь {call.from_user.id} выбрал вариант с отсутствием вывода фото отелей на экран")
        get_final_info(call, is_rejection=True)

    bot.answer_callback_query(callback_query_id=call.id)


@bot.message_handler(state=UserInfoState.count_photo)
def get_count_photo(message: Message) -> None:
    """
    Хэндлер состояния 'count_photo', фиксирует количество выводимых на экран фото отелей в результате поиска,
    присваивает состояние 'final_info'

    :param message: Message
    :return: None
    """
    if message.text.isdigit() and 0 < int(message.text) <= 10:
        bot.set_state(message.from_user.id, UserInfoState.final_information, message.chat.id)
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['count_photo'] = message.text
            logger.info(f"Пользователь {message.from_user.id} ввел необходимое количество фото для каждого отеля: "
                        f"{data['count_photo']}")
        get_final_info(message)

    else:
        bot.send_message(message.from_user.id, 'Необходимо ввести число от 1 до 10')


@bot.message_handler(state=UserInfoState.final_information)
def get_final_info(message, is_rejection: bool = False) -> None:
    """
    Функция вывода информации на экран по результатам опроса пользователя,
    далее запрос к API через функцию hotels() для вывода результатов поиска
    в зависимости от выбранной изначально команды

    :param message: Message
    :param is_rejection: bool
    :return: None
    """
    if is_rejection:
        user_id: Any = message.from_user.id
        chat_id: Any = message.message.chat.id
    else:
        user_id: Any = message.from_user.id
        chat_id: Any = message.chat.id

    with bot.retrieve_data(user_id, chat_id) as data:
        name: str = data['name']
        city: str = data['city']
        location: str = data['location']
        date_arrival = data['date_arrival']
        date_departure = data['date_departure']
        rest_days = date_departure - date_arrival
        count_hotels: str = data['count_hotels']
        count_photo: str = data['count_photo']
        command: str = data['command']
        if data['command'] == '/bestdeal':
            min_price: str = data['min_price']
            max_price: str = data['max_price']
            distance_range: str = data['distance_range']
            bot.send_message(user_id,
                             f'Отлично, опрос окончен.\nСпасибо за предоставленную информацию:\n'
                             f'Ваше имя: {name}\nГород: {city}\nЛокация в городе: {location}\nДата заезда: '
                             f'{date_arrival}\n'
                             f'Дата выезда: {date_departure}\nКоличество дней отдыха: {rest_days.days}\n'
                             f'Минимальная цена за сутки: {min_price}\nМаксимальная цена за сутки: {max_price}\n'
                             f'Расстояние отелей от центра города: {distance_range}\n'
                             f'Количество отелей в результате поиска: {count_hotels}\n'
                             f'Количество выводимых фотографий для каждого отеля: {count_photo}\n'
                             f'Выбранная команда: {command}')
            bot.send_message(user_id, 'Веду поиск...')
            result_info.hotels(user=user_id, chat=chat_id)
        elif data['command'] == '/lowprice' or data['command'] == '/highprice':
            bot.send_message(user_id,
                             f'Отлично, опрос окончен.\nСпасибо за предоставленную информацию:\n'
                             f'Ваше имя: {name}\nГород: {city}\nЛокация в городе: {location}\nДата заезда: '
                             f'{date_arrival}\n'
                             f'Дата выезда: {date_departure}\nКоличество дней отдыха: {rest_days.days}\n'
                             f'Количество отелей в результате поиска: {count_hotels}\n'
                             f'Количество выводимых фотографий для каждого отеля: {count_photo}\n'
                             f'Выбранная команда: {command}')
            bot.send_message(user_id, 'Веду поиск...')
            result_info.hotels(user=user_id, chat=chat_id)

        data['rest_days'] = (date_departure - date_arrival).days
        bot.set_state(user_id, UserInfoState.finish, chat_id)
