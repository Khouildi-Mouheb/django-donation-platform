# messaging/views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .models import Message

User = get_user_model()

@api_view(['POST'])
def save_message(request):
    sender_id = request.data.get("sender_id")
    receiver_id = request.data.get("receiver_id")
    text = request.data.get("text")

    if not sender_id or not receiver_id or not text:
        return Response({"status": "error", "detail": "sender_id, receiver_id and text are required"}, status=400)

    try:
        sender = User.objects.get(id=sender_id)
        receiver = User.objects.get(id=receiver_id)
    except User.DoesNotExist:
        return Response({"status": "error", "detail": "User not found"}, status=404)

    message = Message.objects.create(sender=sender, receiver=receiver, text=text)
    return Response({"status": "ok", "message_id": message.id})







# messaging/views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import get_user_model

User = get_user_model()

def chat_room(request, user_id, receiver_id):
    user = get_object_or_404(User, id=user_id)
    receiver = get_object_or_404(User, id=receiver_id)

    # Optionally load previous messages
    messages = user.sent_messages.filter(receiver=receiver) | user.received_messages.filter(sender=receiver)
    messages = messages.order_by("timestamp")

    return render(request, "messaging/chat_room.html", {
        "user": user,
        "receiver": receiver,
        "messages": messages
    })
