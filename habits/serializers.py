from rest_framework import serializers

from habits.models import Habit
from habits.validators import (
    validate_execution_time,
    validate_periodicity,
    validate_pleasant_habit,
    validate_related_habit,
    validate_reward_or_related_habit,
)


class HabitSerializer(serializers.ModelSerializer):
    """Преобразует привычки в JSON и проверяет бизнес-правила."""

    class Meta:
        model = Habit
        fields = (
            "id",
            "user",
            "place",
            "time",
            "action",
            "is_pleasant",
            "related_habit",
            "periodicity",
            "reward",
            "execution_time",
            "is_public",
        )
        read_only_fields = ("id", "user")

    def validate(self, attrs):
        """Проверяет правила привычки при создании и частичном обновлении."""
        instance = self.instance

        reward = attrs.get(
            "reward",
            getattr(instance, "reward", ""),
        )
        related_habit = attrs.get(
            "related_habit",
            getattr(instance, "related_habit", None),
        )
        execution_time = attrs.get(
            "execution_time",
            getattr(instance, "execution_time", None),
        )
        is_pleasant = attrs.get(
            "is_pleasant",
            getattr(instance, "is_pleasant", False),
        )
        periodicity = attrs.get(
            "periodicity",
            getattr(instance, "periodicity", 1),
        )

        validate_reward_or_related_habit(reward, related_habit)
        validate_execution_time(execution_time)
        validate_related_habit(related_habit)
        validate_pleasant_habit(is_pleasant, reward, related_habit)
        validate_periodicity(periodicity)

        request = self.context.get("request")
        if (
            related_habit
            and request
            and related_habit.user != request.user
        ):
            raise serializers.ValidationError(
                {
                    "related_habit": (
                        "Можно выбрать только собственную приятную привычку."
                    )
                }
            )

        return attrs
