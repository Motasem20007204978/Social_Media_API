from django.db.models.signals import *
from .models import User, Profile, Follow, Block
from django.dispatch import receiver
from notifications_app.tasks import delete_notifications
from .tasks import delete_following_relation, notifying_following


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        print("creating profile...")
        Profile.objects.create(user=instance)


@receiver(pre_save, sender=Follow)
def check_self_following(sender, instance, **kwargs):
    instance.full_clean()


@receiver(pre_save, sender=Block)
def check_self_following(sender, instance, **kwargs):
    instance.full_clean()


@receiver(post_save, sender=Block)
def unfollow(sender, instance, **kwargs):
    delete_following_relation.delay(instance.id)


@receiver(post_save, sender=Follow)
def notify_followed_user(sender, created, instance, **kwargs):
    if created:
        notifying_following.delay(instance.id)


@receiver(post_delete, sender=Follow)
def delete_follow_notification(sender, instance, **kwargs):
    delete_notifications.delay(instance.id, "following_relation_id")
