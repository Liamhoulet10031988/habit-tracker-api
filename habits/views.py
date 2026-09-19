from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from habits.models import Habit
from habits.paginators import HabitPagination
from habits.serializers import HabitSerializer


@extend_schema(tags=["Привычки пользователя"])
class HabitListCreateAPIView(generics.ListCreateAPIView):
    """Показывает привычки пользователя и создаёт новые."""

    serializer_class = HabitSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = HabitPagination

    def get_queryset(self):
        """Возвращает только привычки текущего пользователя."""
        return Habit.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Назначает владельцем привычки текущего пользователя."""
        serializer.save(user=self.request.user)


@extend_schema(tags=["Привычки пользователя"])
class HabitRetrieveUpdateDestroyAPIView(
    generics.RetrieveUpdateDestroyAPIView
):
    """Читает, изменяет и удаляет одну собственную привычку."""

    serializer_class = HabitSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """Не позволяет получить или изменить чужую привычку."""
        return Habit.objects.filter(user=self.request.user)


@extend_schema(tags=["Публичные привычки"])
class PublicHabitListAPIView(generics.ListAPIView):
    """Показывает только публичные привычки без права изменения."""

    queryset = Habit.objects.filter(is_public=True)
    serializer_class = HabitSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = HabitPagination
