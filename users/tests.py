from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import User


class UserAPITestCase(APITestCase):
    """Проверяет регистрацию и получение JWT-токена."""

    def test_user_registration_hashes_password(self):
        response = self.client.post(
            reverse("users:register"),
            {
                "username": "new_user",
                "email": "new@example.com",
                "password": "StrongPassword123",
                "telegram_chat_id": "123456",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email="new@example.com")
        self.assertTrue(user.check_password("StrongPassword123"))
        self.assertEqual(user.telegram_chat_id, "123456")

    def test_duplicate_email_is_rejected(self):
        User.objects.create_user(
            username="first_user",
            email="same@example.com",
            password="StrongPassword123",
        )

        response = self.client.post(
            reverse("users:register"),
            {
                "username": "second_user",
                "email": "same@example.com",
                "password": "StrongPassword123",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_can_receive_jwt_tokens(self):
        User.objects.create_user(
            username="token_user",
            email="token@example.com",
            password="StrongPassword123",
        )

        response = self.client.post(
            reverse("token_obtain_pair"),
            {
                "username": "token_user",
                "password": "StrongPassword123",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    @override_settings(
        CORS_ALLOWED_ORIGINS=["http://localhost:3000"]
    )
    def test_cors_allows_configured_frontend(self):
        response = self.client.options(
            reverse("users:register"),
            HTTP_ORIGIN="http://localhost:3000",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
        )

        self.assertEqual(
            response.headers["Access-Control-Allow-Origin"],
            "http://localhost:3000",
        )

    def test_swagger_documentation_is_available(self):
        response = self.client.get(reverse("swagger-ui"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
