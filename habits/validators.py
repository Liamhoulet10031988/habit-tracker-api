from rest_framework import serializers


def validate_reward_or_related_habit(reward, related_habit):
    """Запрещает одновременно указывать награду и связанную привычку."""
    if reward and related_habit:
        raise serializers.ValidationError(
            "Укажите только вознаграждение или только связанную привычку."
        )


def validate_execution_time(execution_time):
    """Ограничивает время выполнения диапазоном от 1 до 120 секунд."""
    if execution_time is None or not 1 <= execution_time <= 120:
        raise serializers.ValidationError(
            "Время выполнения должно быть от 1 до 120 секунд."
        )


def validate_related_habit(related_habit):
    """Разрешает связывать полезную привычку только с приятной."""
    if related_habit and not related_habit.is_pleasant:
        raise serializers.ValidationError(
            "Связанной может быть только приятная привычка."
        )


def validate_pleasant_habit(is_pleasant, reward, related_habit):
    """Запрещает награду и связь у самой приятной привычки."""
    if is_pleasant and (reward or related_habit):
        raise serializers.ValidationError(
            "У приятной привычки не может быть награды или связи."
        )


def validate_periodicity(periodicity):
    """Разрешает выполнять привычку не реже одного раза в семь дней."""
    if periodicity is None or not 1 <= periodicity <= 7:
        raise serializers.ValidationError(
            "Периодичность должна быть от 1 до 7 дней."
        )
