from email.policy import default
from django.db import models
from uuid import uuid4
from django_extensions.db.models import TimeStampedModel
from django.conf import settings

# Create your models here.

User = settings.AUTH_USER_MODEL


class Notification(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sent_notifs"
    )
    receiver = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="received_notifs"
    )
    data = models.JSONField(null=True, blank=True)
    seen = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"notification from {self.sender.username} to {self.receiver.username}"

    def mark_as_read(self):
        self.seen = True
        self.save()
        return self.seen

    class Meta:
        db_table = "notifications_db"
        ordering = ["-created"]
