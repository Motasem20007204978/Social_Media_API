from django.dispatch import receiver
from django.db.models.signals import post_delete
from .models import Post, Comment, Post
from .tasks import delete_likes


@receiver(post_delete, sender=Post)
def delete_likes_and_comments(sender, instance, **kwargs):
    delete_likes.delay(instance, "post")


@receiver(post_delete, sender=Comment)
def delete_like_and_replies(sender, instance, **kwargs):
    delete_likes.delay(instance, "comment")
