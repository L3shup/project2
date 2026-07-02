import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .database import Chat, Message, User
from .chat_manager import send_message, get_user_chats

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get('user', None)
        if not self.user:
            await self.close()
            return
        self.user_id = self.user.id
        await self.accept()
        # Подписываемся на личный канал пользователя
        await self.channel_layer.group_add(f"user_{self.user_id}", self.channel_name)
        # Подписываемся на все чаты пользователя
        chats = await self.get_user_chats(self.user_id)
        for chat in chats:
            await self.channel_layer.group_add(f"chat_{chat.id}", self.channel_name)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(f"user_{self.user_id}", self.channel_name)
        chats = await self.get_user_chats(self.user_id)
        for chat in chats:
            await self.channel_layer.group_discard(f"chat_{chat.id}", self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')
        if action == 'send_message':
            chat_id = data.get('chat_id')
            text = data.get('text')
            if not chat_id or not text:
                await self.send(json.dumps({'error': 'Missing chat_id or text'}))
                return
            try:
                message = await self.send_message(chat_id, self.user_id, text)
                await self.channel_layer.group_send(
                    f"chat_{chat_id}",
                    {
                        'type': 'chat_message',
                        'message': {
                            'id': message.id,
                            'sender': self.user.username,
                            'text': message.text,
                            'timestamp': message.timestamp.isoformat(),
                        }
                    }
                )
            except Exception as e:
                await self.send(json.dumps({'error': str(e)}))

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'new_message',
            'message': event['message']
        }))

    @database_sync_to_async
    def get_user_chats(self, user_id):
        user = User.objects.get(id=user_id)
        return list(user.chats.all())

    @database_sync_to_async
    def send_message(self, chat_id, sender_id, text):
        return send_message(chat_id, sender_id, text)