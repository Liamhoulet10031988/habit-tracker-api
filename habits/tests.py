from datetime import time, timedelta
from unittest.mock import Mock, patch

import requests
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from habits.models import Habit
from telegram_bot.services import TelegramServiceError, send_telegram_message
from telegram_bot.tasks import build_reminder_text, send_habit_reminders
from users.models import User


class HabitAPITestCase(APITestCase):
    """Проверяет CRUD, доступ, пагинацию и валидаторы привычек."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="owner",
            email="owner@example.com",
            password="StrongPassword123",
        )
        self.other_user = User.objects.create_user(
            username="other",
            email="other@example.com",
            password="StrongPassword123",
        )
        self.client.force_authenticate(user=self.user)

    def habit_data(self, **changes):
        data = {
            "place": "Дом",
            "time": "08:00:00",
            "action": "делать зарядку",
            "is_pleasant": False,
            "periodicity": 1,
            "reward": "Чашка кофе",
            "execution_time": 120,
            "is_public": False,
        }
        data.update(changes)
        return data

    def create_habit(self, user=None, **changes):
        data = self.habit_data(**changes)
        return Habit.objects.create(user=user or self.user, **data)

    def test_authentication_is_required(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(reverse("habits:habit-list-create"))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_habit_assigns_current_user(self):
        response = self.client.post(
            reverse("habits:habit-list-create"),
            self.habit_data(),
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        habit = Habit.objects.get()
        self.assertEqual(habit.user, self.user)

    def test_list_contains_only_own_habits_and_is_paginated(self):
        for number in range(6):
            self.create_habit(action=f"Привычка {number}")
        self.create_habit(
            user=self.other_user,
            action="Чужая привычка",
        )

        response = self.client.get(reverse("habits:habit-list-create"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 6)
        self.assertEqual(len(response.data["results"]), 5)

    def test_public_list_contains_public_habits_only(self):
        self.create_habit(
            user=self.other_user,
            action="Публичная",
            is_public=True,
        )
        self.create_habit(
            user=self.other_user,
            action="Скрытая",
            is_public=False,
        )

        response = self.client.get(reverse("habits:public-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            response.data["results"][0]["action"],
            "Публичная",
        )

    def test_public_list_is_read_only(self):
        response = self.client.post(
            reverse("habits:public-list"),
            self.habit_data(),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def test_user_cannot_retrieve_other_users_habit(self):
        habit = self.create_habit(user=self.other_user)

        response = self.client.get(
            reverse("habits:habit-detail", args=(habit.pk,))
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_can_update_own_habit(self):
        habit = self.create_habit()

        response = self.client.patch(
            reverse("habits:habit-detail", args=(habit.pk,)),
            {"place": "Парк"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        habit.refresh_from_db()
        self.assertEqual(habit.place, "Парк")

    def test_user_can_delete_own_habit(self):
        habit = self.create_habit()

        response = self.client.delete(
            reverse("habits:habit-detail", args=(habit.pk,))
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Habit.objects.filter(pk=habit.pk).exists())

    def test_reward_and_related_habit_cannot_be_selected_together(self):
        pleasant = self.create_habit(
            action="Принять ванну",
            is_pleasant=True,
            reward="",
        )

        response = self.client.post(
            reverse("habits:habit-list-create"),
            self.habit_data(related_habit=pleasant.pk),
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_execution_time_cannot_exceed_120_seconds(self):
        response = self.client.post(
            reverse("habits:habit-list-create"),
            self.habit_data(execution_time=121),
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_related_habit_must_be_pleasant(self):
        useful = self.create_habit(action="Полезная")

        response = self.client.post(
            reverse("habits:habit-list-create"),
            self.habit_data(related_habit=useful.pk, reward=""),
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_pleasant_habit_cannot_have_reward(self):
        response = self.client.post(
            reverse("habits:habit-list-create"),
            self.habit_data(is_pleasant=True),
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_periodicity_cannot_exceed_seven_days(self):
        response = self.client.post(
            reverse("habits:habit-list-create"),
            self.habit_data(periodicity=8),
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_foreign_related_habit_is_rejected(self):
        pleasant = self.create_habit(
            user=self.other_user,
            action="Чужая приятная привычка",
            is_pleasant=True,
            reward="",
        )

        response = self.client.post(
            reverse("habits:habit-list-create"),
            self.habit_data(related_habit=pleasant.pk, reward=""),
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_partial_update_checks_existing_reward(self):
        habit = self.create_habit(reward="Десерт")

        response = self.client.patch(
            reverse("habits:habit-detail", args=(habit.pk,)),
            {"is_pleasant": True},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TelegramServiceTestCase(APITestCase):
    """Проверяет Telegram-сервис и периодическую задачу."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="telegram_user",
            email="telegram@example.com",
            password="StrongPassword123",
            telegram_chat_id="123456",
        )

    def create_current_habit(self, **changes):
        now = timezone.localtime()
        data = {
            "user": self.user,
            "place": "Дом",
            "time": time(now.hour, now.minute),
            "action": "сделать зарядку",
            "periodicity": 1,
            "reward": "Кофе",
            "execution_time": 120,
        }
        data.update(changes)
        return Habit.objects.create(**data)

    def test_build_reminder_text_contains_reward(self):
        habit = self.create_current_habit()

        result = build_reminder_text(habit)

        self.assertIn("сделать зарядку", result)
        self.assertIn("Кофе", result)

    @override_settings(TELEGRAM_BOT_TOKEN="")
    def test_service_requires_bot_token(self):
        with self.assertRaises(TelegramServiceError):
            send_telegram_message("123", "Тест")

    @override_settings(TELEGRAM_BOT_TOKEN="test-token")
    @patch("telegram_bot.services.requests.post")
    def test_service_sends_message(self, post_mock):
        response_mock = Mock()
        response_mock.json.return_value = {"ok": True}
        post_mock.return_value = response_mock

        result = send_telegram_message("123", "Тест")

        self.assertTrue(result["ok"])
        post_mock.assert_called_once()
        response_mock.raise_for_status.assert_called_once()

    @override_settings(TELEGRAM_BOT_TOKEN="test-token")
    @patch("telegram_bot.services.requests.post")
    def test_service_converts_requests_error(self, post_mock):
        post_mock.side_effect = requests.RequestException

        with self.assertRaises(TelegramServiceError):
            send_telegram_message("123", "Тест")

    @patch("telegram_bot.tasks.send_telegram_message")
    def test_task_sends_due_reminder(self, send_mock):
        habit = self.create_current_habit()

        result = send_habit_reminders.run()

        self.assertEqual(result, 1)
        send_mock.assert_called_once()
        habit.refresh_from_db()
        self.assertIsNotNone(habit.last_reminder_sent_at)

    @patch("telegram_bot.tasks.send_telegram_message")
    def test_task_respects_periodicity(self, send_mock):
        habit = self.create_current_habit(periodicity=3)
        habit.last_reminder_sent_at = timezone.now() - timedelta(days=1)
        habit.save(update_fields=("last_reminder_sent_at",))

        result = send_habit_reminders.run()

        self.assertEqual(result, 0)
        send_mock.assert_not_called()

    @patch("telegram_bot.tasks.send_telegram_message")
    def test_task_continues_after_telegram_error(self, send_mock):
        habit = self.create_current_habit()
        send_mock.side_effect = TelegramServiceError("Ошибка")

        result = send_habit_reminders.run()

        self.assertEqual(result, 0)
        habit.refresh_from_db()
        self.assertIsNone(habit.last_reminder_sent_at)
