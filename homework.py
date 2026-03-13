import logging
import os
import sys
import time

from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler
from pprint import pprint
import requests
from requests.exceptions import JSONDecodeError
from telebot import TeleBot, types



load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600*12*360*30
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверка на наличие токенов."""

    if not all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]):
        missing_tokens = []
        if not PRACTICUM_TOKEN:
            missing_tokens.append('PRACTICUM_TOKEN')
        if not TELEGRAM_TOKEN:
            missing_tokens.append('TELEGRAM_TOKEN')
        if not TELEGRAM_CHAT_ID:
            missing_tokens.append('TELEGRAM_CHAT_ID')
        
        logging.CRITICAL(f"Отсутствуют следующие токены: {', '.join(missing_tokens)}")
        raise ValueError(f"Отсутствуют следующие токены: {', '.join(missing_tokens)}")


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
    payload = {'from_date': timestamp-RETRY_PERIOD}
    homework_statuses = requests.get(ENDPOINT, headers=HEADERS, params=payload)

    if homework_statuses.status_code != 200:
        raise Exception(f"Ошибка запроса: {homework_statuses.status_code}")
    
    try:
        response_json = homework_statuses.json()
    except JSONDecodeError as e:
        raise TypeError("Ответ сервера не в формате JSON")
    check_api=check_response(homework_statuses.json())

    return check_api

def check_response(response):
    """Проверяем ответ на наличие всех ключей."""

    if 'homeworks' not in response or 'current_date' not in response:
        logging.error("В ответе отсутствуют ключи 'homeworks' или 'current_date'")
        raise ValueError("В ответе отсутствуют ключи 'homeworks' или 'current_date'")
    
    homeworks = response['homeworks']
    if not isinstance(homeworks, list):
        raise TypeError("Значение по ключу 'homeworks' не является списком")

    if not homeworks:
        logging.debug("Список домашних работ пуст, изменений статуса нет.")
        return {}
    
    for homework in homeworks:
        if not all(key in homework for key in ['date_updated', 'homework_name', 'lesson_name', 'reviewer_comment', 'status']):
            raise ValueError(f"В элементе homeworks отсутствуют необходимые ключи: {', '.join(['date_updated', 'homework_name', 'lesson_name', 'reviewer_comment', 'status'])}")
    return response
    


def parse_status(homework):
    """Определяем статус."""
    if 'homework_name' not in homework:
        logging.error("В ответе API отсутствует ключ 'homework_name'")
        raise KeyError("В ответе API отсутствует ключ 'homework_name'")
                       
    status = homework.get('status')
    if status in HOMEWORK_VERDICTS:
        return HOMEWORK_VERDICTS[status]
    else:
        logging.error(f"Неожиданный статус работы: {status}")
        return f"Неизвестный статус работы: {status}"


def main():
    """Основная логика работы бота."""




    # Создаем объект класса бота
    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    while True:
        try:

            api_answer = get_api_answer(timestamp)
            pprint (api_answer)
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
            maxBytes=1024*1024,
            backupCount=5),
            logging.StreamHandler(sys.stdout)
            ]
        )
    check_tokens()
    main()
