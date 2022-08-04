import os
from dotenv import load_dotenv, find_dotenv
from typing import Dict, Tuple

if not find_dotenv():
    exit('Переменные окружения не загружены, т.к. отсутствует файл .env')
else:
    load_dotenv()

BOT_TOKEN: str = os.getenv('BOT_TOKEN')
RAPID_API_KEY: str = os.getenv('RAPID_API_KEY')
headers: Dict[str, str] = {
    "X-RapidAPI-Key": RAPID_API_KEY,
    "X-RapidAPI-Host": "hotels4.p.rapidapi.com"
}
DEFAULT_COMMANDS: Tuple[tuple[str, str], tuple[str, str]] = (
    ('start', 'Запустить бота'),
    ('help', 'Помощь по командам бота')

)
