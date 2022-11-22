from celery import shared_task
from .models import Like


@shared_task(name="delete_likes_after_deleting")
def delete_likes(instance, ct):
    rel_likes = Like.objects.filter(content_type=ct, object_id=instance.id)
    rel_likes.delete()
