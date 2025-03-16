from django.urls import path
from .views import get_gesture_data

urlpatterns = [
    path("gesture/", get_gesture_data, name="gesture-data"),
]
