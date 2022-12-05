from celery import shared_task
from .models import Comment, Like, Post
from notifications_app.tasks import create_notification


@shared_task(name="delete_likes")
def delete_likes(cid, ct):
    rel_likes = Like.objects.filter(content_type=ct, object_id=cid)
    rel_likes.delete()


@shared_task(name="create_post_notifications")
def notifying_post(instance_id):
    instance = Post.objects.get(id=instance_id)
    for follow_relation in instance.user.followers.all():
        data = {
            "sender_id": instance.user.id,
            "receiver_id": follow_relation.from_user.id,
            "options": {
                "message": f"user {instance.user.full_name} posted on timeline",
                "user_username": instance.user.username,
                "post_id": instance.id,
            },
        }

        create_notification.delay(**data)


@shared_task(name="create_comment_notifications")
def notifying_comment(instance_id):
    instance = Comment.objects.get(id=instance_id)
    # notify comment's user
    receiver = instance.parent.user if instance.parent else instance.post.user
    data = {
        "sender_id": instance.user.id,
        "receiver_id": receiver.id,
        "options": {
            "message": f"user {instance.user.full_name} commented on your post",
            "user_username": instance.user.username,
            "post_id": instance.post.id,
            "comment_id": instance.id,
        },
    }

    create_notification.delay(**data)


@shared_task(name="create_like_notifications")
def notifying_like(instance_id, provider):
    instance = Like.objects.get(id=instance_id)
    if provider == "post":
        related_obj = Post.objects.get(id=instance.object_id)
        receiver = related_obj.user
        options = {
            "message": f"user {instance.user.full_name} liked your post",
            "user_username": instance.user.username,
            "post_id": instance.object_id,
            "like_id": instance.id,
        }
    else:
        related_obj = Comment.objects.get(id=instance.object_id)
        receiver = related_obj.user
        options = {
            "message": f"user {instance.user.full_name} liked your comment",
            "user_username": instance.user.username,
            "reply_id": related_obj.id if related_obj.parent else "",
            "comment_id": related_obj.parent.id
            if related_obj.parent
            else related_obj.id,
            "post_id": related_obj.post.id,
            "like_id": instance.id,
        }
    data = {
        "sender_id": instance.user.id,
        "receiver_id": receiver.id,
        "options": options,
    }
    create_notification.delay(**data)
