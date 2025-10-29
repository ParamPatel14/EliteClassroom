from channels.generic.websocket import AsyncWebsocketConsumer
import json

class WhiteboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f'whiteboard_{self.session_id}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        # Expect messages: {"type": "draw_ops", "ops": [...]} or "clear"
        await self.channel_layer.group_send(self.room_group_name, {
            'type': 'board.message',
            'message': text_data
        })

    async def board_message(self, event):
        await self.send(text_data=event['message'])


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.group = f'chat_{self.session_id}'
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        await self.channel_layer.group_send(self.group, {'type': 'chat.message', 'message': text_data})

    async def chat_message(self, event):
        await self.send(text_data=event['message'])
