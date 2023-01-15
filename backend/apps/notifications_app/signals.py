from django.dispatch import receiver
from django.db.models.signals import *
from .models import Notification
from .tasks import send_client_notification, delete_notification_client_side
from django.db import transaction


@receiver(signal=post_save, sender=Notification)
def send_notification(sender, created, instance, **kwargs):
    if created:
        transaction.on_commit(lambda: send_client_notification.delay(instance.id))


@receiver(post_delete, sender=Notification)
def delete_from_client_side(instance, **kwargs):
    transaction.on_commit(
        lambda: delete_notification_client_side.delay(
            instance.id, instance.receiver.username
        )
    )
