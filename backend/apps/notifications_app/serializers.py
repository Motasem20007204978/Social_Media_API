from rest_framework import serializers
from .models import Notification
from posts_app.serializers import RelatedUser, user_representation
from .tasks import mark_as_read
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample
from drf_queryfields.mixins import QueryFieldsMixin


@extend_schema_serializer(
    exclude_fields=["sender", "receiver"],
    examples=[
        OpenApiExample(
            name="notifications data",
            value={
                "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "sender": user_representation,
                "receiver": user_representation,
                "created": "2022-12-17T14:39:17.902Z",
                "modified": "2022-12-17T14:39:17.902Z",
                "data": {
                    "additionalProp1": "string",
                    "additionalProp2": "string",
                    "additionalProp3": "string",
                },
                "seen": True,
            },
        )
    ],
)
class NotificationSerialzier(QueryFieldsMixin, serializers.ModelSerializer):

    sender = RelatedUser(read_only=True)
    receiver = RelatedUser(read_only=True)

    class Meta:
        model = Notification
        fields = "__all__"
        read_only_fields = ("seen", "data", "created", "modified")

    def update(self, instance, validated_data):
        mark_as_read.delay(instance.id)
        return instance
