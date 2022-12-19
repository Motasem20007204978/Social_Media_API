from channels.generic.websocket import WebsocketConsumer
import json
from asgiref.sync import async_to_sync


class NotificationConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['username']
        self.room_group_name = self.room_name
        async_to_sync(self.channel_layer.group_add)("notifications", self.channel_name)
        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            "notifications", self.channel_name
        )

    def receive(self, text_data=None, bytes_data=None):

        return super().receive(text_data, bytes_data)
