import logging
import random
import time
import os

import redis
import telegram
from environs import Env
from telegram import ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler

from question_parser import parse_questions
from tg_logger import TelegramLogsHandler

logger = logging.getLogger(__name__)

QUESTION, TYPING_REPLY, ANSWER = range(3)


def start(update, context):
    reply_markup = context.bot_data['reply_markup']
    update.message.reply_text('Привет! Я бот для викторин', reply_markup=reply_markup)
    return QUESTION


def handle_new_question_request(update, context):
    questions_and_answers = context.bot_data['questions_and_answers']
    question, answer = random.choice(list(questions_and_answers.items()))

    redis_connection = context.bot_data['redis_connection']

    user_id = update.message.from_user.id

    redis_connection.set(f'question:{user_id}', question)
    redis_connection.set(f'answer:{user_id}', questions_and_answers[question])

    update.message.reply_text(question)
    return ANSWER


def handle_solution_attempt(update, context):
    user_id = update.message.from_user.id
    user_answer = update.message.text.strip().lower()
    redis_connection = context.bot_data['redis_connection']
    reply_markup = context.bot_data['reply_markup']
    last_question = redis_connection.get(f'question:{user_id}')

    correct_answer = redis_connection.get(f'answer:{user_id}')

    if correct_answer:
        correct_answer = correct_answer.split('.')[0].strip().lower()
        correct_answer = correct_answer.split('(')[0].strip().lower()

    if last_question and correct_answer and user_answer == correct_answer.lower():
        update.message.reply_text("Поздравляю! Ваш ответ правильный! Нажмите 'Новый вопрос'", reply_markup=reply_markup)
        return QUESTION
    else:
        update.message.reply_text("К сожалению, ваш ответ неверный. Попробуйте снова!", reply_markup=reply_markup)
        return ANSWER


def handle_surrender(update, context):
    user_id = update.message.from_user.id
    redis_connection = context.bot_data['redis_connection']
    reply_markup = context.bot_data['reply_markup']
    correct_answer = redis_connection.get(f'answer:{user_id}')
    update.message.reply_text(f"Вот правильный ответ: {correct_answer}", reply_markup=reply_markup)
    handle_new_question_request(update, context)
    return QUESTION


def exit_bot(update, context):
    update.message.reply_text("До свидания! Буду рад, если вы вернетесь поиграть снова.")
    return ConversationHandler.END


def main() -> None:
    env = Env()
    env.read_env()

    tg_bot = env.str("TG_BOT_TOKEN")
    tg_bot_logger = env.str("TG_BOT_LOGGER_TOKEN")
    unique_session_id = env.str('TG_CHAT_ID')
    redis_port = env.str("REDIS_PORT")
    redis_password = env.str("REDIS_PASSWORD")
    redis_host = env.str("REDIS_HOST")

    keyboard = [
        ['Новый вопрос', 'Сдаться'],
        ['Мой счёт']
    ]

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    file_path = os.path.join("questions", "1vs1298.txt")
    questions_and_answers = parse_questions(file_path)

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
            updater = Updater(tg_bot)
            redis_connection = redis.Redis(host=redis_host, port=redis_port,
                                           password=redis_password, db=0, decode_responses=True)

            dispatcher = updater.dispatcher

            dispatcher.bot_data['redis_connection'] = redis_connection
            dispatcher.bot_data['reply_markup'] = reply_markup
            dispatcher.bot_data['questions_and_answers'] = questions_and_answers

            conv_handler = ConversationHandler(
                entry_points=[CommandHandler('start', start)],

                states={
                    QUESTION: [MessageHandler(Filters.regex('^Новый вопрос$'), handle_new_question_request)],

                    ANSWER: [MessageHandler(Filters.text & ~Filters.command & ~Filters.regex('^Сдаться'),
                                            handle_solution_attempt,
                                            pass_user_data=True),
                             MessageHandler(Filters.regex('^Сдаться'), handle_surrender)
                             ],

                },

                fallbacks=[CommandHandler("done", exit_bot)]
            )

            dispatcher.add_handler(conv_handler)


            updater.start_polling()
            updater.idle()

        except Exception:
            logger.exception('Телеграм-бот упал с ошибкой:')
            time.sleep(5)


if __name__ == '__main__':
    main()