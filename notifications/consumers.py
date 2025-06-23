import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Only allow staff users to connect
        if self.scope["user"].is_anonymous or not self.scope["user"].is_staff:
            await self.close()
            return

        # Join the admin notification group
        self.group_name = 'admin_notifications'
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to admin notifications'
        }))

    async def disconnect(self, close_code):
        # Leave the admin notification group
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        # Handle any incoming WebSocket messages if needed
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')

            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'message': 'Connection alive'
                }))
        except json.JSONDecodeError:
            pass

    # Handle notification from group
    async def new_contact_notification(self, event):
        # Send notification to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'new_contact',
            'data': event['data']
        }))

    # Handle notification count updates
    async def notification_count_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'count_update',
            'data': event['data']
        }))
