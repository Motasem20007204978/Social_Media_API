from __future__ import absolute_import, unicode_literals
from celery import shared_task
from django.core.management import call_command
from .models import Notification
from django.contrib.auth import get_user_model
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

User = get_user_model()
channel_layer = get_channel_layer()


@shared_task(name="clear_read_notifications")
def clear_notifications():
    call_command("clearreadnotifications")
    return True


@shared_task(name="mark_notification_as_read")
def mark_as_read(notif_id):
    notif = Notification.objects.get(id=notif_id)
    return notif.mark_as_read()


@shared_task(name="create_notifications")
def create_notification(sender_id, receiver_id, options: dict = None):
    data = {
        "sender": User.objects.get(id=sender_id),
        "receiver": User.objects.get(id=receiver_id),
        "data": options,
    }
    Notification.objects.create(**data)
    return f"notification created"


@shared_task(name="send_notifications")
def send_client_notification(notif_id):
    notif = Notification.objects.get(id=notif_id)
    payload = {
        "type": "send.notification",
        "notification_id": str(notif.id),
        "sender_id": str(notif.sender.id),
        "data": notif.data,
        "is_read": notif.seen,
    }
    async_to_sync(channel_layer.group_send)(notif.receiver.username, payload)
    return "notification sent successfully"


@shared_task(name="load_notifications")
def load_related_notifications(username):
    notifs = Notification.objects.filter(receiver__username=username)
    for notif in notifs:
        send_client_notification.delay(notif_id=notif.id)


@shared_task(name="delete_instance_notification")
def delete_notifications(obj_id, search_word: str):
    notifications = Notification.objects.filter(data__contains={search_word: obj_id})
    notifications.delete()


@shared_task(name="delete_from_client_side")
def delete_notification_client_side(notif_id, client_username):
    async_to_sync(channel_layer.group_send)(
        client_username,
        {
            "type": "delete.notification",  # necessary to select method in consumer class
            "notification_id": notif_id,
        },
    )
    return "delete notification alert is sent successfully"
