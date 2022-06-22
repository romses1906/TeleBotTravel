from keyboards.reply.contact import request_contact
from loader import bot
from states.contact_information import UserInfoState
from telebot.types import Message


@bot.message_handler(commands=['lowprice', 'highprice', 'bestdeal'])
def survey(message: Message) -> None:
    bot.set_state(message.from_user.id, UserInfoState.name, message.chat.id)
    bot.send_message(message.from_user.id, f'Привет, {message.from_user.username}, введи свое имя')

    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['command'] = message.text


@bot.message_handler(state=UserInfoState.name)
def get_name(message: Message) -> None:
    if message.text.isalpha():
        bot.send_message(message.from_user.id,
                         'Спасибо, записал. Теперь введите город, в котором будет производиться поиск отелей')
        bot.set_state(message.from_user.id, UserInfoState.city, message.chat.id)

        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['name'] = message.text
    else:
        bot.send_message(message.from_user.id, 'Имя может содержать только буквы')


@bot.message_handler(state=UserInfoState.city)
def get_city(message: Message) -> None:
    bot.send_message(message.from_user.id,
                     'Спасибо, записал. Выберите дату заезда в отель')
    bot.set_state(message.from_user.id, UserInfoState.date_arrival, message.chat.id)

    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['city'] = message.text


@bot.message_handler(state=UserInfoState.date_arrival)
def get_date_arrival(message: Message) -> None:
    bot.send_message(message.from_user.id,
                     'Спасибо, записал. Выберите дату выезда из отеля')
    bot.set_state(message.from_user.id, UserInfoState.date_departure, message.chat.id)

    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['date_arrival'] = message.text


@bot.message_handler(state=UserInfoState.date_departure)
def get_date_departure(message: Message) -> None:
    bot.send_message(message.from_user.id, 'Спасибо, записал')

    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['date_departure'] = message.text
        if data['command'] == '/bestdeal':
            bot.send_message(message.from_user.id,
                             f'Введите диапазон цен для поиска подходящих отелей')
            bot.set_state(message.from_user.id, UserInfoState.price_range, message.chat.id)
        elif data['command'] == '/lowprice' or data['command'] == '/highprice':
            bot.send_message(message.from_user.id,
                             f'Введи количество отелей, которое необходимо вывести в результате, но не более 5')
            bot.set_state(message.from_user.id, UserInfoState.count_hotels, message.chat.id)


# для bestdeal
@bot.message_handler(state=UserInfoState.price_range)
def get_price_range(message: Message) -> None:
    bot.send_message(message.from_user.id,
                     'Спасибо, записал. Введите диапазон расстояния отелей от центра города для поиска')
    bot.set_state(message.from_user.id, UserInfoState.distance_range, message.chat.id)

    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['price_range'] = message.text


@bot.message_handler(state=UserInfoState.distance_range)
def get_distance_range(message: Message) -> None:
    bot.send_message(message.from_user.id, f'Спасибо, записал.'
                                           f'Введите количество отелей, которое необходимо вывести в результате, но не более 5')
    bot.set_state(message.from_user.id, UserInfoState.count_hotels, message.chat.id)

    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['distance_range'] = message.text


@bot.message_handler(state=UserInfoState.count_hotels)
def get_count_hotels(message: Message) -> None:
    if message.text.isdigit() and int(message.text) <= 5:
        bot.send_message(message.from_user.id,
                         'Спасибо, записал. Необходимо ли вывести фотографии найденных отелей? Да/Нет')
        bot.set_state(message.from_user.id, UserInfoState.photo, message.chat.id)

        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['count_hotels'] = message.text
    else:
        bot.send_message(message.from_user.id, 'Количество искомых отелей необходимо ввести числом не более 5')


@bot.message_handler(state=UserInfoState.photo)
def get_photo(message: Message) -> None:
    if message.text == 'Да':
        bot.send_message(message.from_user.id,
                         'Спасибо, записал. Введите количество необходимых фото для каждого найденного отеля, но не более 10')
        bot.set_state(message.from_user.id, UserInfoState.count_photo, message.chat.id)

        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['photo'] = message.text
    else:
        bot.send_message(message.from_user.id, 'Спасибо, записал, фото не нужны')


@bot.message_handler(state=UserInfoState.count_photo)
def get_count_photo(message: Message) -> None:
    if int(message.text) <= 10:
        bot.send_message(message.from_user.id, f'Спасибо, записал. '
                                               f'Необходимо вывести {int(message.text)} фото для каждого найденного отеля ')
        # bot.set_state(message.from_user.id, UserInfoState.count_photo, message.chat.id)

        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['count_photo'] = message.text
    else:
        bot.send_message(message.from_user.id, 'Необходимо ввести число не более 10')
