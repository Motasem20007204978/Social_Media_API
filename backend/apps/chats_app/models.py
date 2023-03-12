from django.db import models
from notifications_app.models import AbstractMessagingModel
from django_extensions.db.models import TimeStampedModel
from django.db.models.signals import pre_save
from django.conf import settings
from uuid import uuid4
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from asgiref.sync import sync_to_async

# Create your models here.


class NameValidator(RegexValidator):
    regex = r"^\w+-\w+$"
    message = "enter name with expression 'username-username'"
    flags = 0


name_validator = NameValidator()

User = get_user_model()


class ChatRoom(models.Model):
    id = models.UUIDField(
        max_length=50, primary_key=True, default=uuid4, editable=False
    )
    name = models.CharField(max_length=50, unique=True, validators=[name_validator])
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, max_length=2, editable=False
    )
    ...

    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        return super().save(*args, **kwargs)

    class Meta:
        db_table = "rooms_db"


class Message(AbstractMessagingModel):

    room = models.ForeignKey(
        to=ChatRoom, on_delete=models.CASCADE, related_name="chat_messages"
    )

    def __str__(self) -> str:
        return f"message from {self.sender.username} to room {self.room.name}"

    class Meta:
        db_table = "messages_db"
