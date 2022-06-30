from telebot.handler_backends import State, StatesGroup

class UserInfoState(StatesGroup):
    name = State()
    age = State()
    country = State()
    city = State()
    phone_number = State()
    date_arrival = State()
    date_departure = State()
    count_hotels = State()
    photo = State()
    count_photo = State()
    price_range = State()
    distance_range = State()
    command = State()