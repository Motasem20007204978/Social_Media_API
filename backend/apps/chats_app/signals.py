from django.dispatch import receiver
from django.db.models.signals import *
from .models import ChatRoom, User, Message
from asgiref.sync import async_to_sync
from .tasks import send_client_message, delete_message_client_side
from django.db.transaction import on_commit


@receiver(pre_save, sender=ChatRoom)
def sort_name(instance, **kwargs):
    keys = instance.name.split("-")
    usernames = sorted(keys)
    instance.name = "-".join(usernames)


async def get_users(room_name):
    usernames = room_name.split("-")
    users = await User.objects.ain_bulk(sorted(usernames), field_name="username")
    return users


@receiver(pre_save, sender=ChatRoom)
def check_room_users(instance, **kwargs):
    users = async_to_sync(get_users)(instance.name)
    if not users.__len__() == 2:
        raise Exception("room must contain tow existing users")


@receiver(post_save, sender=ChatRoom)
def add_users(instance, **kwargs):
    users = async_to_sync(get_users)(instance.name)
    for user in users.values():
        instance.users.add(user)


@receiver(post_save, sender=Message)
def send_room_message(instance, **kwargs):
    on_commit(lambda: send_client_message.delay(instance.id))


@receiver(post_delete, sender=Message)
def delete_room_message(instance, **kwargs):
    on_commit(lambda: delete_message_client_side.delay(instance.id, instance.room.name))
