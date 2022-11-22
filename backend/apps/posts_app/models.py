from functools import cached_property
from django.db import models
from django_extensions.db.models import ModificationDateTimeField, CreationDateTimeField
import os
from uuid import uuid4
from django.utils.deconstruct import deconstructible
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from uuid import uuid4
from django.conf import settings
from rest_framework.validators import ValidationError

User = settings.AUTH_USER_MODEL


@deconstructible
class PathAndRename(object):
    def __init__(self, sub_path):
        self.path = sub_path

    def __call__(self, instance, filename):
        ext = filename.split(".")[-1]
        filename = "{}.{}".format(uuid4().hex, ext)
        print(self.path)
        return os.path.join(self.path, filename)


class TextualObject(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    text = models.TextField(max_length=500)
    created_at = CreationDateTimeField()
    updated_at = ModificationDateTimeField()

    @cached_property
    def likes(self):
        return Like.objects.filter(object_id=self.id, content_type="post")

    class Meta:
        ordering = ["-created_at"]
        abstract = True


class Post(TextualObject):
    @cached_property
    def count_comments(self):
        return self.comments.count()

    class Meta:
        db_table = "posts_db"


class Comment(TextualObject):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies"
    )

    @property
    def count_replies(self):
        return self.replies.count()

    class Meta:
        db_table = "comments_db"


class Like(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    TYPES = [("post", "post"), ("comment", "comment")]
    content_type = models.CharField(max_length=10, choices=TYPES)
    object_id = models.UUIDField(editable=False)

    def validate_unique(self, *args, **kwargs) -> None:
        try:
            return super().validate_unique(*args, **kwargs)
        except:
            raise ValidationError("cannot like the same object more than one time")

    def clean(self) -> None:
        return super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    class Meta:
        indexes = [  # to search quickly by these fields
            models.Index(fields=["content_type", "object_id"]),
        ]
        unique_together = ["user", "object_id", "content_type"]
        db_table = "likes_db"


class Attachment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(
        upload_to=PathAndRename("post_files/"), blank=True, null=True
    )

    def clean(self) -> None:
        if self.post.attachments.count() == 2:
            raise ValidationError("cannot add more than 2 files for a post")
        return super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    class Meta:
        db_table = "attachemnts_db"
        order_with_respect_to = "post"  # orders the attachemnts for one post
