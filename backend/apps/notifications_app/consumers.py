from channels.generic.websocket import JsonWebsocketConsumer
import json
from channels.exceptions import DenyConnection
from asgiref.sync import async_to_sync
from .tasks import load_related_notifications


class NotificationConsumer(JsonWebsocketConsumer):
    def connect(self):

        self.user = self.scope["user"]
        self.group_name = str(self.user.username)
        self.accept()
        async_to_sync(self.channel_layer.group_add)(self.group_name, self.channel_name)
        load_related_notifications.delay(self.group_name)

    def disconnect(self, close_code=None):
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name, self.channel_name
        )
        pass

    def send_notification(self, payload):
        self.send_json(content=payload)

    def delete_notification(self, event):
        event["action"] = "delete"
        self.send_json(event)
