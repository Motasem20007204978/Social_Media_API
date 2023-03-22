from channels.generic.websocket import JsonWebsocketConsumer
from asgiref.sync import async_to_sync
from .tasks import load_realted_messages, create_db_message, delete_db_message


class ChatConsumer(JsonWebsocketConsumer):
    def connect(self):

        self.user = self.scope["user"]
        print(self.user)
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        async_to_sync(self.channel_layer.group_add)(self.room_name, self.channel_name)
        load_realted_messages.delay(self.room_name)
        super().connect()

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_name, self.channel_name
        )
        return super().disconnect(code)

    def receive_json(self, content, **kwargs):
        if content.get("type") == "create":
            message_data = {
                "room_name": self.room_name,
                "sender_id": str(self.scope["user"].id),
                "options": {"message": content["message"]},
            }
            self.send_json(message_data)
            create_db_message.delay(**message_data)
            print("hello")

        elif content.get("type") == "delete":
            message_id = content.get("message_id")
            delete_db_message.delay(message_id)

    def send_message(self, event):
        event["action"] = "send"
        self.send_json(event)

    def delete_message(self, event):
        event["action"] = "delete"
        self.send_json(event)
