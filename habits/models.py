from django.conf import settings
from django.db import models


class Habit(models.Model):
    """Полезная или приятная привычка пользователя."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="habits",
        verbose_name="Пользователь",
    )
    place = models.CharField(max_length=200, verbose_name="Место")
    time = models.TimeField(verbose_name="Время")
    action = models.CharField(max_length=255, verbose_name="Действие")
    is_pleasant = models.BooleanField(
        default=False,
        verbose_name="Приятная привычка",
    )
    related_habit = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="useful_habits",
        verbose_name="Связанная привычка",
    )
    periodicity = models.PositiveSmallIntegerField(
        default=1,
        verbose_name="Периодичность в днях",
    )
    reward = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Вознаграждение",
    )
    execution_time = models.PositiveSmallIntegerField(
        verbose_name="Время выполнения в секундах",
    )
    is_public = models.BooleanField(
        default=False,
        verbose_name="Публичная привычка",
    )
    last_reminder_sent_at = models.DateTimeField(
        blank=True,
        null=True,
        editable=False,
        verbose_name="Последнее напоминание",
    )

    class Meta:
        ordering = ("time", "pk")
        verbose_name = "Привычка"
        verbose_name_plural = "Привычки"

    def __str__(self):
        return f"Я буду {self.action} в {self.time:%H:%M} в {self.place}"
