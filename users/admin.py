from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Показывает пользователей и Telegram chat ID в админ-панели."""

    fieldsets = UserAdmin.fieldsets + (
        ("Telegram", {"fields": ("telegram_chat_id",)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Контакты", {"fields": ("email", "telegram_chat_id")}),
    )
    list_display = ("username", "email", "telegram_chat_id", "is_active")
