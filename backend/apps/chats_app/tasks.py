from __future__ import absolute_import, unicode_literals
from celery import shared_task
from .models import Message, ChatRoom
from django.contrib.auth import get_user_model
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

User = get_user_model()
channel_layer = get_channel_layer()


@shared_task(name="create_message")
def create_db_message(room_name, sender_id, options: dict = None):
    data = {
        "room": ChatRoom.objects.get(name=room_name),
        "sender": User.objects.get(id=sender_id),
        "data": options,
    }
    Message.objects.create(**data)
    return f"message created"


@shared_task(name="send_message")
def send_client_message(message_id):
    message = Message.objects.get(id=message_id)
    payload = {
        "type": "send_message",
        "message_id": str(message_id),
        "sender": message.sender.username,
        "data": message.data,
    }
    async_to_sync(channel_layer.group_send)(message.room.name, payload)
    return "Chat sent successfully"


@shared_task(name="load_messages")
def load_realted_messages(room_name):
    messages = Message.objects.filter(room__name=room_name)
    for message in messages:
        send_client_message.delay(str(message.id))


@shared_task(name="delete_message")
def delete_db_message(message_id):
    messages = Message.objects.filter(id=message_id)
    messages.delete()


@shared_task(name="delete_from_client_side")
def delete_message_client_side(message_id, room_name):
    async_to_sync(channel_layer.group_send)(
        room_name,
        {
            "type": "delete_message",
            "message_id": message_id,
        },
    )
    return "delete message alert is sent successfully"
