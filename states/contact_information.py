from telebot.handler_backends import State, StatesGroup


class UserInfoState(StatesGroup):
    name = State()
    city = State()
    date_arrival = State()
    date_departure = State()
    count_hotels = State()
    photo = State()
    count_photo = State()
    min_price = State()
    max_price = State()
    distance_range = State()
    command = State()
    rest_days = State()
    location = State()
    location_id = State()
    final_information = State()
    hotel_id = State()
