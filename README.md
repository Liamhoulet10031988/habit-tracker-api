# Habit Tracker API

Backend SPA-приложения для формирования полезных привычек. Пользователь может
создавать полезные и приятные привычки, назначать награду, связывать полезную
привычку с приятной и получать напоминания в Telegram.

## Возможности

- регистрация пользователей;
- JWT-авторизация и обновление токена;
- создание, просмотр, изменение и удаление собственных привычек;
- отдельный список публичных привычек;
- пагинация `limit/offset` по пять записей;
- проверка правил полезных и приятных привычек;
- периодические задачи Celery;
- отправка напоминаний через Telegram Bot API;
- настройка CORS для подключения SPA-фронтенда;
- Swagger и ReDoc для документации API;
- тесты и отчёт покрытия.

## Основные технологии

- Python 3.12;
- Django и Django REST Framework;
- Simple JWT;
- drf-spectacular;
- Celery и Redis;
- PostgreSQL или SQLite для локального запуска;
- Telegram Bot API;
- Poetry.

## Структура проекта

```text
habit-tracker-api/
├── config/          # настройки Django, маршруты и Celery
├── habits/          # привычки, API и валидаторы
├── telegram_bot/    # Telegram API и периодическая задача
├── users/           # пользователь и регистрация
├── .env.template    # пример переменных окружения
├── manage.py        # команды Django
├── pyproject.toml   # зависимости проекта
└── README.md
```

## Правила привычек

- одновременно нельзя указывать награду и связанную привычку;
- выполнение занимает не более 120 секунд;
- связанной может быть только приятная привычка текущего пользователя;
- у приятной привычки не бывает награды и связанной привычки;
- периодичность составляет от одного до семи дней.

## Установка

Клонируйте репозиторий и установите зависимости:

```powershell
git clone https://github.com/Liamhoulet10031988/habit-tracker-api.git
cd habit-tracker-api
poetry install
```

Создайте локальный файл `.env` по примеру `.env.template`:

```powershell
Copy-Item .env.template .env
```

Заполните в `.env` собственные значения. Секретный ключ Django, пароль
PostgreSQL и токен Telegram-бота нельзя публиковать.

Если переменные `POSTGRES_*` не заданы, проект использует локальную SQLite.
Для PostgreSQL заранее создайте базу `habit_tracker` и укажите данные
подключения в `.env`.

## Telegram-бот

1. Откройте в Telegram `@BotFather`.
2. Выполните команду `/newbot`.
3. Сохраните полученный токен в `TELEGRAM_BOT_TOKEN` файла `.env`.
4. Запишите идентификатор чата пользователя в поле `telegram_chat_id`.

Токен хранится только в `.env` и не должен попадать в Git.

## Запуск

Примените миграции и запустите Django:

```powershell
poetry run python manage.py migrate
poetry run python manage.py runserver
```

В отдельных терминалах запустите Redis, Celery worker и Celery beat:

```powershell
redis-server
poetry run celery -A config worker -l INFO -P eventlet
poetry run celery -A config beat -l INFO
```

Celery beat каждую минуту проверяет время привычек. Сообщение отправляется,
если наступило заданное время и после предыдущего напоминания прошло число
дней, указанное в поле `periodicity`.

## Эндпоинты

| Метод | Адрес | Назначение |
|---|---|---|
| `POST` | `/api/users/register/` | регистрация |
| `POST` | `/api/token/` | получение access- и refresh-токенов |
| `POST` | `/api/token/refresh/` | обновление access-токена |
| `GET`, `POST` | `/api/habits/` | список своих привычек и создание |
| `GET`, `PATCH`, `PUT`, `DELETE` | `/api/habits/<id>/` | работа со своей привычкой |
| `GET` | `/api/habits/public/` | список публичных привычек |
| `GET` | `/api/schema/` | OpenAPI-схема |
| `GET` | `/api/docs/` | Swagger UI |
| `GET` | `/api/redoc/` | ReDoc |

Для защищённых запросов передавайте access-токен:

```text
Authorization: Bearer <access-токен>
```

Пример создания полезной привычки:

```json
{
  "place": "Дом",
  "time": "08:00:00",
  "action": "делать зарядку",
  "is_pleasant": false,
  "related_habit": null,
  "periodicity": 1,
  "reward": "Чашка кофе",
  "execution_time": 120,
  "is_public": true
}
```

## Проверки

```powershell
poetry run python manage.py check
poetry run python manage.py makemigrations --check --dry-run
poetry run python manage.py test
poetry run coverage run manage.py test
poetry run coverage report -m
poetry run coverage html -d coverage_html
poetry run isort . --check-only
poetry run flake8 . --exclude=.venv,migrations
```

HTML-отчёт покрытия создаётся локально в `coverage_html/index.html` и не
публикуется, потому что его можно заново получить одной командой.
