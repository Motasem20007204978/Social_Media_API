from channels.generic.websocket import WebsocketConsumer
import json
from channels.exceptions import DenyConnection
from asgiref.sync import async_to_sync


class NotificationConsumer(WebsocketConsumer):
    def connect(self):
        if self.scope["user"].is_anonymous:
            raise DenyConnection("Invalid user")

        self.user = self.scope["user"]
        self.group_name = str(self.user.username)
        async_to_sync(self.channel_layer.group_add)(self.group_name, self.channel_name)
        self.accept()

    def receive(self, text_data=None, bytes_data=None):
        print(text_data)
        self.send(text_data)
        return super().receive(text_data, bytes_data)

    def disconnect(self, close_code=None):
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name, self.channel_name
        )
        pass

    def send_notification(self, payload):
        self.send(text_data=json.dumps(payload))

    def delete_notification(self, event):
        notif_id = event.get("notification_id")
        payload = json.dumps({"action": "delete", "notification_id": notif_id})
        self.send(text_data=payload)
