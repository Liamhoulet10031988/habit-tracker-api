from rest_framework.pagination import LimitOffsetPagination


class HabitPagination(LimitOffsetPagination):
    """Выводит по пять привычек и поддерживает limit/offset."""

    default_limit = 5
    max_limit = 20
