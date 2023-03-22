from django.contrib.auth import get_user_model
import re
from .models import ChatRoom
from .signals import get_users
from channels.middleware import BaseMiddleware

User = get_user_model()


class RoomMiddleware(BaseMiddleware):
    async def name_exp_validation(self, room_name):
        if not re.search(r"^(\w+)-(\w+)$", room_name):
            raise Exception("room name must be with username-username expression")

    async def create_room(self, room_name):
        chat_room = await ChatRoom.objects.aget_or_create(name=room_name)
        return chat_room

    async def check_users(self, room_name):
        users = await get_users(room_name)
        if not users.__len__() == 2:
            raise Exception(
                'group name must contain 2 usernames in exp "username-username"'
            )

    async def check_authorization(self, room_name, username):
        users = await get_users(room_name)
        if not users.get(username):
            raise Exception("cannot authorize to connect with this room")

    async def __call__(self, scope, receive, send):
        scope = dict(scope)
        room_name = scope["path"].split("/")[-1]
        await self.name_exp_validation(room_name)
        await self.check_users(room_name)
        await self.check_authorization(room_name, scope["user"].username)
        await self.create_room(room_name)
        return await super().__call__(scope, receive, send)
