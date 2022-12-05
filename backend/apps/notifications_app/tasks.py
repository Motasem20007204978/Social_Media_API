from __future__ import absolute_import, unicode_literals
from celery import shared_task
from django.core.management import call_command
from .models import Notification
from django.contrib.auth import get_user_model

User = get_user_model()


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
def send_notification(notif_id):
    ...


@shared_task(name="delete_instance_notification")
def delete_notifications(obj_id, search_word: str):
    notifications = Notification.objects.filter(data__contains={search_word: obj_id})
    notifications.delete()
    ...
