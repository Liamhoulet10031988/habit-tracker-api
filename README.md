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

## Запуск через Docker Compose

Требуются Docker Engine с Compose v2 либо Docker Desktop. Создайте `.env`
из `.env.template`, замените SECRET_KEY и пароль новой базы на собственные.
Не перезаписывайте уже настроенный `.env`.

```powershell
docker compose up --build -d --wait --wait-timeout 180
```

Команда собирает приложение и запускает PostgreSQL, Redis, Django/Gunicorn,
Celery worker, Celery beat и Nginx. Документация:
http://127.0.0.1:8087/api/docs/ . Корневой URL `/` не является страницей API.

Внутри Compose `POSTGRES_HOST` переопределяется на `db`, `REDIS_URL` — на
`redis://redis:6379/0`. Для ручного запуска Python вне Docker используются
`localhost` из `.env`. Создавать базу вручную для Compose не требуется.
Telegram-напоминания требуют настоящего `TELEGRAM_BOT_TOKEN` и chat ID.

Все ресурсы имеют собственный префикс `habit-tracker-api`. Четыре тома хранят
PostgreSQL, Redis, собранную статику и расписание Celery beat. Nginx читает
статику и конфигурацию без права записи. Наружу опубликован только порт Nginx;
по умолчанию он слушает `127.0.0.1:8087`. Адрес и порт задаются в `.env`.
Контейнеры имеют ограничения памяти, ротацию логов и автоматический перезапуск.

```powershell
docker compose ps
docker compose exec -T web python manage.py check
docker compose exec -T web python manage.py test --noinput
docker compose exec -T nginx nginx -t
docker compose logs --tail=80 web nginx celery_worker celery_beat
```

Данные сохраняются при обычном пересоздании контейнеров. Не используйте
`docker compose down -v` для остановки сервиса с нужными данными.

## CI/CD и удалённое развёртывание

Развёрнутый API: https://orangepi5b.taila2acdb.ts.net:8443/api/docs/ .
Схема OpenAPI: https://orangepi5b.taila2acdb.ts.net:8443/api/schema/ .
Образы: https://hub.docker.com/r/liamhoulet/habit-tracker-api .
API требует регистрации и JWT для операций с личными привычками.

`.github/workflows/ci.yml` выполняет последовательность
`Tests → Linters → Docker image → Deploy`. Тесты используют временные
PostgreSQL и Redis. Ошибка любого этапа останавливает последующие.

При push в `feature/habit-tracker-deployment` либо `develop` образ публикуется
в Docker Hub с тегами SHA коммита и `latest`, после чего точный SHA доставляется
на сервер. Для Pull Request выполняется проверочная сборка без публикации
и deploy. Для проверки всей цепочки нужен успешный **push-запуск**, не PR-запуск.

Сборка и deploy используют ARM64 runner `ubuntu-24.04-arm` для Orange Pi.
Для сервера x86_64 нужно выбрать runner `ubuntu-latest` в обоих jobs.

### Подготовка сервера

1. Установите Docker Engine и Compose v2 или новее; включите запуск Docker
   при старте системы. Проверьте архитектуру командой `uname -m`.
2. Создайте отдельный каталог `/home/orangepi/habit-tracker-api` с правами700.
   Не используйте каталог, базу, порт или том другого приложения.
3. Сохраните в нём приватный `.env` с правами600 по шаблону. Укажите
   `DOCKER_IMAGE=habit-tracker-api:local`, отдельные SECRET_KEY и пароль БД,
   реальные ALLOWED_HOSTS и CSRF_TRUSTED_ORIGINS. Для LAN при необходимости
   задайте `HTTP_BIND_ADDRESS=0.0.0.0`, сохранив HTTP_PORT=8087.
4. Подготовьте на сервере образы `postgres:16-alpine`, `redis:7-alpine`,
   `nginx:1.29-alpine`. Deploy не меняет общие настройки Docker daemon.
5. Подключите сервер к Tailscale. CI-тегу разрешите только TCP22 этого сервера.
6. Добавьте публичную часть отдельного SSH-ключа в authorized_keys сервера.
   Через уже доверенное SSH-соединение получите `/etc/ssh/ssh_host_ed25519_key.pub`.
   Закрытый ключ не добавляйте в репозиторий.
7. Создайте публичный репозиторий `habit-tracker-api` в Docker Hub и токен
   с правом Read & Write без Delete. Настройте Secrets **до первого push**.

### GitHub Secrets

В репозитории откройте Settings → Secrets and variables → Actions:

| Secret | Значение |
| --- | --- |
| DOCKERHUB_USERNAME | логин Docker Hub |
| DOCKERHUB_TOKEN | токен публикации Docker Hub |
| TAILSCALE_AUTHKEY | ephemeral reusable auth key с ограниченным CI-тегом |
| SSH_HOST | Tailscale IP сервера |
| SSH_USER | пользователь SSH |
| SSH_PORT | обычно22 |
| SSH_PRIVATE_KEY | отдельный закрытый SSH-ключ |
| SSH_KNOWN_HOSTS | `TAILSCALE_IP ssh-ed25519 PUBLIC_HOST_KEY` |
| DEPLOY_PATH | `/home/orangepi/habit-tracker-api` |

Secrets другого репозитория автоматически не используются. Не публикуйте
пароли, токены, `.env` и закрытые ключи в коде либо логах.

Runner получает опубликованный образ, сжимает `docker save` и передаёт его
через проверенный SSH в `docker load`. На сервере меняется только DOCKER_IMAGE
в `.env`; Compose запускает доставленную версию с `--no-build --pull never`.
После миграций и collectstatic проверяется готовность Django, перечитывается
upstream Nginx и выполняется HTTP-запрос к `/api/docs/`.

Для публичного доступа домашнего сервера можно использовать отдельный порт
HTTPS Tailscale Funnel, не изменяя уже настроенные сайты. Для HTTPS-origin
администратора обязательно заполните CSRF_TRUSTED_ORIGINS со схемой и портом.
Nginx сохраняет исходную HTTPS-схему Funnel через X-Forwarded-Proto; Django
учитывает её через SECURE_PROXY_SSL_HEADER для корректных ссылок пагинации.
Такая настройка рассчитана на доверенный прокси: не публикуйте Gunicorn
и не выставляйте внутренний HTTP-вход в обход HTTPS-прокси без проверки схемы.
Не открывайте наружу PostgreSQL, Redis или Gunicorn. Полный результат подтверждают
успешные четыре jobs push-запуска и работающая ссылка приложения.
