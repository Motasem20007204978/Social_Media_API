from distutils.command.install_scripts import install_scripts
from django.dispatch import receiver
from django.db.models.signals import *
from .models import Notification
from .tasks import send_notification


@receiver(signal=post_save, sender=Notification)
def send_notification(sender, created, instance, **kwargs):
    if created:
        send_notification.delay(instance)
