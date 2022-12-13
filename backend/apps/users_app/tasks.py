from __future__ import absolute_import, unicode_literals

from celery import shared_task
import time
from django.conf import settings
from .utils import activation_url
from rest_framework.generics import get_object_or_404
from django.core.management import call_command
from django.contrib.auth import get_user_model
from notifications_app.tasks import create_notification
from .models import Block, Follow, Profile, User
from django.db.models import Q


@shared_task
def add(x, y):
    time.sleep(5)
    return x + y


@shared_task(name="create_user_profile")
def create_user_profile(uid):
    user = User.objects.get(id=uid)
    Profile.objects.create(user=user)
    return "profile created"


@shared_task(name="delete_inactivated_users")
def delete_inactivated_users():
    call_command(command_name="deleteinactivatedaccounts")
    return True


@shared_task(name="delete_expired_tokens")
def delete_expired_tokens():
    call_command(command_name="flushexpiredtokens")


@shared_task(name="send_email_activation")
def send_activation(data):
    User = get_user_model()
    email = data.get("email", "")
    user = get_object_or_404(User, email=email)
    uuid = user.generate_uuid()
    token = user.generate_token()
    url_name = data.get("url_name", "activate-email")
    url = activation_url(url_name, uuid, token)
    subject = "email activation link"
    message = f"checking email url is \n {url}"
    user.email_user(subject, message)
    return f"email activation is sent"


@shared_task(name="create_following_notification")
def notifying_following(follow_obj_id):
    follow_obj = Follow.objects.get(id=follow_obj_id)
    data = {
        "sender_id": follow_obj.from_user.id,
        "receiver_id": follow_obj.to_user.id,
        "options": {
            "message": f"user {follow_obj.from_user.full_name} started following you",
            "follwer_id": follow_obj.from_user.id,
            "following_relation_id": follow_obj.id,
        },
    }
    create_notification.delay(**data)
    return "notification creating..."


@shared_task(name="delete_following_relation")
def delete_following_relation(block_id):
    block_obj = Block.objects.get(id=block_id)
    try:
        follow_rel = Follow.objects.filter(
            Q(from_user=block_obj.from_user, to_user=block_obj.to_user)
            | Q(from_user=block_obj.to_user, to_user=block_obj.from_user)
        )
        follow_rel.delete()
    except follow_rel.DoesNotExist:
        return "there is no following relation"
