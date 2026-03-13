import logging
import os
import sys
import time

from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler
import requests
from requests.exceptions import JSONDecodeError
from telebot import TeleBot

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
    if (PRACTICUM_TOKEN is None
        ) or (
            TELEGRAM_TOKEN is None) or (
                TELEGRAM_CHAT_ID is None):
        logging.critical("Проверь наличие токенов")
        raise ValueError("Проверь наличие токенов")


def send_message(bot, message):
    """Отправка сообщения в Телеграмм-бот."""
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
        )
        logging.debug(f"Сообщение успешно отправлено: {message}")
    except Exception as e:
        logging.error(f"Ошибка при отправке сообщения: {e}")


def get_api_answer(timestamp):
    """Отправляем запрос."""
    payload = {'from_date': timestamp}
    try:
        homework_statuses = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=payload)
        homework_statuses.raise_for_status()
    except requests.RequestException as error_request:
        logging.error(f"Ошибка запроса: {homework_statuses.status_code}")
        raise error_request
    try:
        response_json = homework_statuses.json()
    except JSONDecodeError as error_json:
        logging.error("Ошибка типа ответа на запрос")
        raise TypeError(error_json)

    check_api = check_response(response_json)
    return check_api


def check_response(response):
    """Проверяем ответ на наличие всех ключей."""
    if not isinstance(response, dict):
        raise TypeError("Ответ от запроса не словарь")
    if ('homeworks' not in response) or ('current_date' not in response):
        logging.error(
            "В ответе отсутствуют ключи 'homeworks' или 'current_date'")
        raise ValueError(
            "В ответе отсутствуют ключи 'homeworks' или 'current_date'")
    homeworks = response['homeworks']
    if not isinstance(homeworks, list):
        raise TypeError("Значение по ключу 'homeworks' не является списком")
    for homework in homeworks:
        if not all(key in homework for key in ['homework_name', 'status']):
            raise ValueError(
                "В элементе homeworks отсутствуют необходимые ключи")
    return response


def parse_status(homework):
    """Определяем статус."""
    if 'homework_name' not in homework:
        logging.error("В ответе API отсутствует ключ 'homework_name'")
        raise KeyError("В ответе API отсутствует ключ 'homework_name'")
    verdict = homework.get('status')
    homework_name = homework.get('homework_name')
    if verdict in HOMEWORK_VERDICTS:
        return f'Изменился статус проверки работы "{
            homework_name}". {HOMEWORK_VERDICTS[verdict]}'
    else:
        logging.error(f"Неожиданный статус работы: {verdict}")
        raise ValueError(f"Неизвестный статус работы: {verdict}")


def main():
    """Основная логика работы бота."""
    check_tokens()
    # Создаем объект класса бота
    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    while True:
        try:
            api_answer = get_api_answer(timestamp - RETRY_PERIOD)
            if api_answer['homeworks'] == []:
                logging.debug("Нет изменений в статусе домашних работ.")
            message = parse_status(api_answer['homeworks'][0])
            send_message(bot, message)
        except Exception as error:
            logging.error(f"Сбой в работе программы: {error}")
            message = f'Сбой в работе программы: {error}'
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
