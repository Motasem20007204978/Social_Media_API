from django.db.models.signals import *
from .models import User, Follow, Block
from django.dispatch import receiver
from notifications_app.tasks import delete_notifications
from .tasks import (
    delete_following_relation,
    notifying_following,
    send_activation,
)
from django.db import transaction


@receiver(post_save, sender=User)
def send_email_activation(instance, created, **kwargs):
    if created and not instance.is_active:
        data = {"email": instance.email}
        transaction.on_commit(lambda: send_activation.delay(data))


@receiver(pre_save, sender=Follow)
def check_self_following(sender, instance, **kwargs):
    instance.full_clean()


@receiver(pre_save, sender=Block)
def check_self_following(sender, instance, **kwargs):
    instance.full_clean()


@receiver(post_save, sender=Block)
def unfollow(created, instance, **kwargs):
    if created:
        transaction.on_commit(lambda: delete_following_relation.delay(instance.id))


@receiver(post_save, sender=Follow)
def notify_followed_user(sender, created, instance, **kwargs):
    if created:
        transaction.on_commit(lambda: notifying_following.delay(instance.id))


@receiver(post_delete, sender=Follow)
def delete_follow_notification(sender, instance, **kwargs):
    delete_notifications.delay(instance.id, "following_relation_id")
