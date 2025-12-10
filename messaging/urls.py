# messaging/urls.py
from django.urls import path
from .views import save_message, chat_room

urlpatterns = [
    path("save/", save_message, name="save_message"),
    path("chat/<int:user_id>/<int:receiver_id>/", chat_room, name="chat_room"),
]
