import requests
from requests import Response
from typing import Dict
from loguru import logger

logger.add('debug.log', level='DEBUG', format="{time} {level} {message}", rotation="08:00",
           compression="zip")


def get_request(url: str, headers: Dict[str, str], params: Dict[str, str]) -> Response:
    """
    Функция для выполнения запроса к API

    :param url: передается адрес для запроса
    :param headers: передаются key и host для запроса
    :param params: передаются необходимые параметры для запроса
    :return: Response
    """

    try:
        response: Response = requests.get(url=url, headers=headers, params=params, timeout=10)
        if response.status_code == requests.codes.ok:  # почитать, что это значит
            return response
    except requests.exceptions.RequestException as exc:
        logger.exception(exc)
