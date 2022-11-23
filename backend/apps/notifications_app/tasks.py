from __future__ import absolute_import, unicode_literals
from celery import shared_task
from django.core.management import call_command

@shared_task(name="clear_read_notifications")
def clear_notifications():
    call_command("clearreadnotifications")
    return True

@shared_task(name='mark_notif_as_read')
def mark_as_read(notif):
    return notif.mark_as_read()
    