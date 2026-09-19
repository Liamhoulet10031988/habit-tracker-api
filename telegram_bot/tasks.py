import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from habits.models import Habit
from telegram_bot.services import (
    TelegramServiceError,
    send_telegram_message,
)

logger = logging.getLogger(__name__)


def build_reminder_text(habit):
    """Собирает понятный текст напоминания о привычке."""
    text = f"Напоминание: я буду {habit.action} в {habit.place}."
    if habit.related_habit:
        text += f" После этого: {habit.related_habit.action}."
    elif habit.reward:
        text += f" Вознаграждение: {habit.reward}."
    return text


@shared_task
def send_habit_reminders():
    """Отправляет наступившие напоминания и возвращает их количество."""
    now = timezone.localtime()
    habits = Habit.objects.select_related(
        "user",
        "related_habit",
    ).filter(
        time__hour=now.hour,
        time__minute=now.minute,
    ).exclude(user__telegram_chat_id="")

    sent_count = 0
    for habit in habits:
        reminder_period = timedelta(days=habit.periodicity)
        if (
            habit.last_reminder_sent_at
            and now - habit.last_reminder_sent_at < reminder_period
        ):
            continue

        try:
            send_telegram_message(
                habit.user.telegram_chat_id,
                build_reminder_text(habit),
            )
        except TelegramServiceError as exc:
            logger.error("Не удалось отправить напоминание: %s", exc)
            continue

        habit.last_reminder_sent_at = now
        habit.save(update_fields=("last_reminder_sent_at",))
        sent_count += 1

    return sent_count
