from peewee import *
from datetime import datetime

db = SqliteDatabase('history.db')


class History(Model):
    """
    Класс для создания модели таблицы в базе данных. Родительский класс - Model

    """

    uid = CharField()
    location = CharField()
    hotel_name = CharField()
    site = CharField()
    address = CharField()
    name_label_1 = CharField()
    distance_from_label_1 = CharField()
    name_label_2 = CharField()
    distance_from_label_2 = CharField()
    price = FloatField()
    full_price = FloatField()
    rest_days = IntegerField()
    hotel_id = IntegerField()
    command = CharField()
    date = DateTimeField(default=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    class Meta:
        """
        Класс для определения базы данных для созданной модели

        """
        database = db
