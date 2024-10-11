import logging
import random
import time

import redis
import telegram
from environs import Env
import vk_api
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id

from scripts import parse_questions, open_file
from tg_logger import TelegramLogsHandler

logger = logging.getLogger(__name__)

QUESTION, ANSWER = range(2)


def start(user_id, vk, keyboard):
    vk.messages.send(
        user_id=user_id,
        message='Привет! Я бот для викторин. Выберите действие: Новый вопрос или Сдаться',
        keyboard=keyboard.get_keyboard(),
        random_id=get_random_id()
    )
    return QUESTION


def handle_new_question_request(user_id, vk, redis_connection, keyboard):
    file_contents = open_file("questions/1vs1298.txt")
    questions_and_answers = parse_questions(file_contents)

    question, answer = random.choice(list(questions_and_answers.items()))

    redis_connection.set(f'question:{user_id}', question)
    redis_connection.set(f'answer:{user_id}', answer)

    vk.messages.send(
        user_id=user_id,
        message=question,
        keyboard=keyboard.get_keyboard(),
        random_id=get_random_id()
    )
    return ANSWER


def handle_solution_attempt(user_id, user_answer, vk, redis_connection, keyboard):
    last_question = redis_connection.get(f'question:{user_id}')
    correct_answer = redis_connection.get(f'answer:{user_id}')

    if correct_answer:
        correct_answer = correct_answer.split('.')[0].strip().lower()
        correct_answer = correct_answer.split('(')[0].strip().lower()

    if last_question and correct_answer and user_answer == correct_answer.lower():
        vk.messages.send(
            user_id=user_id,
            message="Поздравляю! Ваш ответ правильный! Нажмите 'Новый вопрос'",
            keyboard=keyboard.get_keyboard(),
            random_id=get_random_id()
        )
        return QUESTION
    else:
        vk.messages.send(
            user_id=user_id,
            message="К сожалению, ваш ответ неверный. Попробуйте снова!",
            keyboard=keyboard.get_keyboard(),
            random_id=get_random_id()
        )
        return ANSWER


def handle_surrender(user_id, vk, redis_connection, keyboard):
    correct_answer = redis_connection.get(f'answer:{user_id}')
    vk.messages.send(
        user_id=user_id,
        message=f"Вот правильный ответ: {correct_answer}",
        keyboard=keyboard.get_keyboard(),
        random_id=get_random_id()
    )
    handle_new_question_request(user_id, vk, redis_connection, keyboard)
    return QUESTION


def done(user_id, vk):
    vk.messages.send(
        user_id=user_id,
        message="До свидания! Буду рад, если вы вернетесь поиграть снова.",
        random_id=get_random_id()
    )
    return None


def main() -> None:
    env = Env()
    env.read_env()

    vk_token = env.str("VK_BOT_TOKEN")
    redis_port = env.str("REDIS_PORT")
    redis_password = env.str("REDIS_PASSWORD")
    redis_host = env.str("REDIS_HOST")
    tg_bot_logger = env.str("TG_BOT_LOGGER_TOKEN")
    unique_session_id = env.str('TG_CHAT_ID')

    vk_session = vk_api.VkApi(token=vk_token)
    vk = vk_session.get_api()

    keyboard = VkKeyboard(one_time=True)

    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)

    longpoll = VkLongPoll(vk_session)

    tg_bot_logger = telegram.Bot(token=tg_bot_logger)

    telegram_handler = TelegramLogsHandler(tg_bot_logger, unique_session_id)
    telegram_handler.setLevel(logging.INFO)
    telegram_formatter = logging.Formatter('%(message)s')
    telegram_handler.setFormatter(telegram_formatter)

    logger.addHandler(telegram_handler)
    logger.setLevel(logging.INFO)
    logger.info('Запуск бота')

    while True:
        try:
            redis_connection = redis.Redis(host=redis_host, port=redis_port,
                                           password=redis_password, db=0, decode_responses=True)
            for event in longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    user_message = event.text.strip().lower()
                    user_id = event.user_id

                    if user_message == "привет" or user_message == "начать":
                        start(user_id, vk, keyboard)

                    elif user_message == "новый вопрос":
                        handle_new_question_request(user_id, vk, redis_connection, keyboard)

                    elif user_message == "сдаться":
                        handle_surrender(user_id, vk, redis_connection, keyboard)

                    else:
                        handle_solution_attempt(user_id, user_message, vk, redis_connection, keyboard)

                time.sleep(0.1)

        except Exception as e:
            logger.exception('ВК-бот упал с ошибкой:')
            time.sleep(5)


if __name__ == '__main__':
    main()