from rest_framework import serializers
from .models import Attachment, Post, Comment, Like
from rest_framework.generics import get_object_or_404
from drf_writable_nested.serializers import WritableNestedModelSerializer
from drf_base64.fields import Base64FileField
from drf_spectacular.utils import (
    extend_schema_serializer,
    OpenApiExample,
)
from drf_queryfields.mixins import QueryFieldsMixin


user_representation = {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "username": "string",
    "full_name": "string",
    "picture": "example.com/media/profile_pic/32435223-2532.jpg",
}


class RelatedUser(serializers.RelatedField):
    def to_representation(self, value):
        bostedBy = {
            "id": value.id,
            "username": value.username,
            "full_name": value.full_name,
            "picture": value.profile.profile_pic.url,
        }
        return bostedBy


like_representation = {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "user": user_representation,
    "content_type": "post",
    "object_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
}


@extend_schema_serializer(
    exclude_fields=["user"],
    examples=[
        OpenApiExample(name="like data", value=like_representation, response_only=True)
    ],
)
class LikeSerializer(serializers.ModelSerializer):
    user = RelatedUser(read_only=True)

    class Meta:
        model = Like
        fields = ["id", "user", "content_type", "object_id"]
        read_only_fields = ["id", "user", "object_id", "content_type"]

    def create(self, validated_data):

        request = self.context["request"]
        validated_data["user"] = request.user

        pid = request.GET.get("post_id", "")
        cid = request.GET.get("comment_id", "")
        rid = request.GET.get("reply_id", "")

        def fill_fields(oid, ct):
            validated_data["object_id"] = oid
            validated_data["content_type"] = ct

        if pid:
            fill_fields(pid, "post")
        elif cid:
            fill_fields(cid, "comment")
        elif rid:
            fill_fields(rid, "comment")

        return super().create(validated_data)


comment_representation = {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "user": user_representation,
    "post": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "parent": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "text": "string",
    "count_likes": 30,
    "count_replies": 50,
    "created": "2022-12-13T17:26:25.901Z",
    "modified": "2022-12-13T17:26:25.901Z",
}


@extend_schema_serializer(
    exclude_fields=["user", "count_likes", "count_replies"],
    examples=[
        OpenApiExample(
            name="comment data", value=comment_representation, response_only=True
        )
    ],
)
class CommentSerializer(QueryFieldsMixin, serializers.ModelSerializer):
    user = RelatedUser(read_only=True)
    post = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Comment
        fields = (
            "id",
            "user",
            "post",
            "parent",
            "text",
            "count_likes",
            "count_replies",
            "created",
            "modified",
        )
        read_only_fields = ("id", "user", "post", "parent")

    @property
    def request(self):
        request = self.context["request"]
        return request

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if representation.get("parent", ""):
            del representation["count_replies"]
        else:
            del representation["parent"]
        return representation

    def create(self, validated_data):
        validated_data["user"] = self.request.user
        validated_data["post"] = get_object_or_404(
            Post, pk=self.request.resolver_match.kwargs.get("post_id")
        )
        comment_id = self.request.GET.get("comment_id", "")
        if comment_id:
            validated_data["parent"] = get_object_or_404(Comment, id=comment_id)
        return super().create(validated_data)


class AttachmentSerializer(serializers.ModelSerializer):

    file = Base64FileField(required=False)

    class Meta:
        model = Attachment
        fields = ("id", "file")
        read_only_fields = ("id",)


post_representation = {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "user": user_representation,
    "text": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "count_likes": 30,
    "count_comments": 50,
    "attachments": [
        {
            "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            "file": "example.com/post_pic/453532-o4f532.jpg",
        }
    ],
    "created": "2022-12-13T17:26:25.901Z",
    "modified": "2022-12-13T17:26:25.901Z",
}


@extend_schema_serializer(
    exclude_fields=["user", "count_likes", "count_comments"],
    examples=[
        OpenApiExample(
            name="post data",
            value=post_representation,
            response_only=True,
            status_codes=[200, 201],
        )
    ],
)
class PostFeedSerializer(QueryFieldsMixin, WritableNestedModelSerializer):
    user = RelatedUser(read_only=True)
    attachments = AttachmentSerializer(many=True)

    class Meta:
        model = Post
        fields = [
            "id",
            "user",
            "text",
            "count_likes",
            "count_comments",
            "attachments",
            "created",
            "modified",
        ]
        read_only_fields = ["id", "user"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        post = super().create(validated_data)
        return post
