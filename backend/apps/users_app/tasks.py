from __future__ import absolute_import, unicode_literals

from celery import shared_task
import time
from django.conf import settings
from .utils import activation_url
from rest_framework.generics import get_object_or_404
from django.core.management import call_command
from django.contrib.auth import get_user_model


@shared_task
def add(x, y):
    time.sleep(5)
    return x + y


@shared_task(name="delete_inactivated_users")
def delete_inactivated_users():
    call_command(command_name="delete_inactivated_accounts")
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
