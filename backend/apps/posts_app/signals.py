from django.dispatch import receiver
from django.db.models.signals import post_delete, post_save, pre_delete
from .models import Like, Post, Comment
from .tasks import delete_likes, notifying_post, notifying_like
from notifications_app.tasks import delete_notifications
from django.db import transaction


@receiver(post_delete, sender=Post)
def delete_post_likes(sender, instance, **kwargs):
    delete_likes.delay(instance.id, "post")


@receiver(post_delete, sender=Comment)
def delete_comment_like(instance, **kwargs):
    delete_likes.delay(instance.id, "comment")


@receiver(post_save, sender=Post)
def notify_posting(sender, instance, created, **kwargs):
    if created:
        transaction.on_commit(lambda: notifying_post.delay(instance.id))


@receiver(post_delete, sender=Post)
def delete_post_notifications(sender, instance, **kwargs):
    delete_notifications.delay(instance.id, "post_id")


@receiver(post_save, sender=Like)
def create_like_notification(created, instance, **kwargs):
    if created:
        transaction.on_commit(
            lambda: notifying_like.delay(instance.id, instance.content_type)
        )


@receiver(post_delete, sender=Like)
def delete_like_notification(instance, **kwargs):
    print(instance.id)
    delete_notifications.delay(instance.id, "like_id")


# pre_delete is for replies to be deletd before delete comment
@receiver(pre_delete, sender=Comment)
def delete_comment_notification(instance, **kwargs):
    print("parent", instance.parent)
    if instance.parent:
        print("dlete reply", instance.id)
        search_word = "reply_id"
    search_word = "comment_id"
    delete_notifications.delay(instance.id, search_word)
