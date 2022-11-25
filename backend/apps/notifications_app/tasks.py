from __future__ import absolute_import, unicode_literals
from celery import shared_task
from django.core.management import call_command
from .models import Notification


@shared_task(name="clear_read_notifications")
def clear_notifications():
    call_command("clearreadnotifications")
    return True


@shared_task(name="mark_notification_as_read")
def mark_as_read(notif):
    return notif.mark_as_read()


@shared_task(name="create_notifications")
def create_notifications(sender, receiver, options: dict = None):
    data = {
        "sender": sender,
        "receiver": receiver,
        "data": options,
    }
    Notification.objects.acreate(**data)
    return f"notification created"


@shared_task(name="send_notifications")
def send_notification(obj):
    ...
