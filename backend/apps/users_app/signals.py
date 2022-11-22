from django.db.models.signals import *
from .models import User, Profile, Follow, Block
from django.dispatch import receiver


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(pre_save, sender=Follow)
def check_self_following(sender, instance, **kwargs):
    instance.full_clean()


@receiver(pre_save, sender=Block)
def check_self_following(sender, instance, **kwargs):
    instance.full_clean()


@receiver(post_save, sender=Block)
def unfollow(sender, instance, **kwargs):
    try:
        follow_rel = Follow.objects.get(
            from_user=instance.from_user, to_user=instance.to_user
        )
        follow_rel.delete()
    except:
        ...
