import logging
import os
import sys
import time
from http import HTTPStatus
from logging.handlers import RotatingFileHandler

import requests
from dotenv import load_dotenv
from requests.exceptions import JSONDecodeError
from telebot import TeleBot

from exceptions import (ApiJsonError, ApiRequestError,
                        IsinstanceError, MessageError, ValueKeyError)

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверка на наличие токенов."""
    tokens = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID
    }
    for token_name, token_value in tokens.items():
        if token_value is None:
            var_errors = "Отсутствует токен: " + token_name
            logging.critical(var_errors)
            raise ValueError(var_errors)


def send_message(bot, message):
    """Отправка сообщения в Телеграмм-бот."""
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
        )
        logging.debug(f"Сообщение успешно отправлено: {message}")
    except Exception as error:
        raise MessageError(f"Ошибка при отправке сообщения: {error}")


def get_api_answer(timestamp):
    """Отправляем запрос."""
    payload = {'from_date': timestamp}
    try:
        homework_statuses = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=payload)
        if homework_statuses.status_code != HTTPStatus.OK:
            raise ApiRequestError(
                f"Ошибка запроса: {homework_statuses.status_code}")
        homework_statuses.raise_for_status()
    except requests.RequestException:
        raise ApiRequestError(
            f"Ошибка запроса: {homework_statuses.status_code}")
    try:
        response_json = homework_statuses.json()
    except JSONDecodeError as error_json:
        raise ApiJsonError(error_json)
    return response_json


def check_response(response):
    """Проверяем ответ на наличие всех ключей."""
    if not isinstance(response, dict):
        raise IsinstanceError("Ответ от запроса не словарь")
    if ('homeworks' not in response) or ('current_date' not in response):
        raise ValueKeyError(
            "В ответе отсутствуют ключи 'homeworks' или 'current_date'")
    homeworks = response['homeworks']
    if not isinstance(homeworks, list):
        raise IsinstanceError(
            "Значение по ключу 'homeworks' не является списком")
    return response


def parse_status(homework):
    """Определяем статус."""
    if 'homework_name' not in homework:
        raise ValueKeyError("В ответе API отсутствует ключ 'homework_name'")
    verdict = homework.get('status')
    homework_name = homework.get('homework_name')
    if verdict in HOMEWORK_VERDICTS:
        return f'Изменился статус проверки работы "{
            homework_name}". {HOMEWORK_VERDICTS[verdict]}'
    raise ValueKeyError(f"Неизвестный статус работы: {verdict}")


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    while True:
        try:
            api_answer = get_api_answer(timestamp - RETRY_PERIOD)
            check_response(api_answer)
            timestamp = api_answer['current_date']
            if not api_answer['homeworks']:
                logging.debug("Нет изменений в статусе домашних работ.")
            else:
                message = parse_status(api_answer['homeworks'][0])
                send_message(bot, message)
        except MessageError as message_error:
            logging.error(message_error)
        except Exception as exception_error:
            message = f'Сбой в работе логики программы:  + {str(
                exception_error)}'
            logging.error(message)
            send_message(bot, message)
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[RotatingFileHandler(
            'bot.log',
            maxBytes=1024 * 1024,
            backupCount=5),
            logging.StreamHandler(sys.stdout)])
    main()
