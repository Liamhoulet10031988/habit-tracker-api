from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.permissions import AllowAny

from users.serializers import UserRegistrationSerializer


@extend_schema(
    summary="Регистрация пользователя",
    description="Создаёт пользователя и сохраняет пароль в виде хеша.",
    tags=["Пользователи"],
)
class UserCreateAPIView(generics.CreateAPIView):
    """Регистрирует нового пользователя."""

    serializer_class = UserRegistrationSerializer
    permission_classes = (AllowAny,)
