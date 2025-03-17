from django.urls import re_path
from .consumers2 import GestureRecognitionConsumer

websocket_urlpatterns = [
    re_path(r'ws/gesture/$', GestureRecognitionConsumer.as_asgi()),
]
