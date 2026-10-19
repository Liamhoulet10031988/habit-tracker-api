from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Пользователь сервиса с идентификатором чата Telegram."""

    email = models.EmailField(unique=True, verbose_name="Электронная почта")
    telegram_chat_id = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="ID чата Telegram",
    )

    def __str__(self):
        return self.email
