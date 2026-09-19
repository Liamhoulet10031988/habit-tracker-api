from django.urls import path

from habits.views import (
    HabitListCreateAPIView,
    HabitRetrieveUpdateDestroyAPIView,
    PublicHabitListAPIView,
)

app_name = "habits"

urlpatterns = [
    path("", HabitListCreateAPIView.as_view(), name="habit-list-create"),
    path("public/", PublicHabitListAPIView.as_view(), name="public-list"),
    path(
        "<int:pk>/",
        HabitRetrieveUpdateDestroyAPIView.as_view(),
        name="habit-detail",
    ),
]
