from rest_framework import serializers

from users.models import User


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Проверяет данные и создаёт пользователя с хешированным паролем."""

    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "password",
            "telegram_chat_id",
        )
        read_only_fields = ("id",)

    def create(self, validated_data):
        """Создаёт пользователя через create_user для хеширования пароля."""
        return User.objects.create_user(**validated_data)
