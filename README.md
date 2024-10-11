# VK и Telegram Бот с Квизом

Этот проект включает два бота: один для VK и один для Telegram. Боты представляют собой квиз для пользователей и логирования ошибок в Telegram.

## Описание

- **VK Бот**: [Бот для VK, с квизом](https://vk.com/club227360436)
- **TG Бот**: [Бот для TG, с квизом](https://t.me/devmantest_bot)
- **Telegram Логгер**: Бот для Telegram, который отправляет логи ошибок и информацию о работе VK бота в указанный чат.

Вопросы и ответы для квиза можно найти в папке questions

## Установка

1. Клонируйте репозиторий:
   ```bash
   https://github.com/ArtemZinukov/quiz.git

2. Установите зависимости:

    ```bash
       pip install -r requirements.txt

## Настройка

Создайте файл .env в корневом каталоге проекта и добавьте следующие переменные окружения:

 - VK_BOT_TOKEN= ваш токен бота VK
 - TG_BOT_TOKEN= ваш токен бота Telegram
 - TG_CHAT_ID= ваш ID чата Telegram
 - TG_BOT_LOGGER_TOKEN= ваш токен логгера Telegram
 - REDIS_PORT= порт для бд redis
 - REDIS_PASSWORD= пароль для бд redis
 - REDIS_HOST= хост для бд redis

## Запуск

Для запуска бота выполните следующую команду:

```
python tg_bot.py
```

Или, если вы хотите запустить VK бота:

```
python vk_bot.py
```