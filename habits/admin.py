from django.contrib import admin

from habits.models import Habit


@admin.register(Habit)
class HabitAdmin(admin.ModelAdmin):
    """Настраивает отображение привычек в админ-панели."""

    list_display = (
        "action",
        "user",
        "time",
        "periodicity",
        "is_pleasant",
        "is_public",
    )
    list_filter = ("is_pleasant", "is_public", "periodicity")
    search_fields = ("action", "place", "user__email")
