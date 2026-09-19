import requests
from django.conf import settings


class TelegramServiceError(Exception):
    """Ошибка отправки сообщения через Telegram API."""


def send_telegram_message(chat_id, message):
    """Отправляет одно сообщение пользователю Telegram."""
    if not settings.TELEGRAM_BOT_TOKEN:
        raise TelegramServiceError("Не настроен TELEGRAM_BOT_TOKEN.")

    url = (
        "https://api.telegram.org/"
        f"bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    )
    try:
        response = requests.post(
            url,
            data={"chat_id": chat_id, "text": message},
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise TelegramServiceError(
            "Telegram API не принял сообщение."
        ) from exc

    return response.json()
