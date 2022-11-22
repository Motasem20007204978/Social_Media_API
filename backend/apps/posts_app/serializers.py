from rest_framework import serializers
from .models import Attachment, Post, Comment, Like
from rest_framework.generics import get_object_or_404
from drf_writable_nested.serializers import WritableNestedModelSerializer
from drf_base64.fields import Base64FileField
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes


@extend_schema_field(field=OpenApiTypes.OBJECT)
class RelatedUser(serializers.RelatedField):
    def to_representation(self, value):
        bostedBy = {
            "id": value.id,
            "username": value.username,
            "full_name": value.full_name,
            "picture": value.profile.profile_pic.url,
        }
        return bostedBy


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


class CommentSerializer(serializers.ModelSerializer):
    user = RelatedUser(read_only=True)
    likes = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    post = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Comment
        fields = (
            "id",
            "user",
            "post",
            "parent",
            "text",
            "likes",
            "count_replies",
            "created_at",
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


class PostFeedSerializer(WritableNestedModelSerializer):
    user = RelatedUser(read_only=True)
    attachments = AttachmentSerializer(many=True)
    likes = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Post
        fields = [
            "id",
            "user",
            "text",
            "created_at",
            "likes",
            "count_comments",
            "attachments",
        ]
        read_only_fields = ["id", "user"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        post = super().create(validated_data)
        return post
