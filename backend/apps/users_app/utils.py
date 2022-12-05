from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.utils.http import urlsafe_base64_decode
from rest_framework.generics import get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from .models import Block
from django.db.models import Q

User = get_user_model()


def activation_url(url_name, uuid64, token):
    site = Site.objects.get_current()
    current_domain = site.domain
    relative_url = reverse(url_name, kwargs={"uuid": uuid64, "token": token})
    actiavation_link = f"http://{current_domain}{relative_url}"
    return actiavation_link
    ...


def get_user_from_uuid(uuid):
    uid = urlsafe_base64_decode(uuid).decode()
    user = get_object_or_404(User, id=uid)
    return user


def check_block_relation(sender, receiver):
    block_list = Block.objects.filter(
        Q(from_user=sender, to_user=receiver) | Q(from_user=receiver, to_user=sender)
    )
    return block_list.exists()
