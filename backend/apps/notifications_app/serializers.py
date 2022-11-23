from shutil import ReadError
from rest_framework import serializers
from .models import Notification
from posts_app.serializers import RelatedUser
from .tasks import mark_as_read


class NotificationSerialzier(serializers.ModelSerializer):

    sender = RelatedUser(read_only=True)
    receiver = RelatedUser(read_only=True)

    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ('seen', 'data', 'created', 'modified')
    
    def update(self, instance, validated_data):
        mark_as_read.delay(instance)
        return instance     
