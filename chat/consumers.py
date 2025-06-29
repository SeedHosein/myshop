import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async # For DB operations
from django.contrib.auth import get_user_model
from .models import ChatMessage, ChatSession
from django.utils import timezone

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        self.user = self.scope['user']

        # Basic validation: Ensure room_name (ChatSession ID) exists or is valid UUID
        try:
            self.chat_session = await database_sync_to_async(
                ChatSession.objects.select_related('support_agent').get
            )(id=self.room_name)
        except (ChatSession.DoesNotExist, ValueError):
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # If user is staff and not already agent, assign them if session has no agent
        if self.user.is_authenticated and self.user.is_staff:
            if not self.chat_session.support_agent:
                self.chat_session.support_agent = self.user
                await database_sync_to_async(self.chat_session.save)()
                await self.send_system_message(f"Support agent {self.user.email} joined the chat.")

        # Send existing messages to the connecting user
        # This could be part of a separate 'fetch_history' message type for more control
        messages = await database_sync_to_async(list)(
            ChatMessage.objects.filter(session=self.chat_session).order_by('timestamp').select_related('sender')
        )
        for msg_obj in messages:
            sender_email = msg_obj.sender.email if msg_obj.sender else "System"
            sender_is_staff = msg_obj.sender.is_staff if msg_obj.sender else False
            await self.send(text_data=json.dumps({
                'type': 'chat_message',
                'message': msg_obj.message,
                'sender_email': sender_email,
                'sender_is_staff': sender_is_staff,
                'timestamp': msg_obj.timestamp.isoformat(),
            }))

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        # Optionally, notify if a support agent leaves
        if self.user.is_authenticated and self.user.is_staff and self.chat_session.support_agent == self.user:
             await self.send_system_message(f"Support agent {self.user.email} left the chat.")
             # self.chat_session.support_agent = None # Or reassign, or mark as needing agent
             # await database_sync_to_async(self.chat_session.save)() 

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_text = text_data_json['message']

        if not self.user.is_authenticated:
            # Handle unauthenticated users if you allow guest chat (e.g. store with session_id)
            # For now, we assume authentication via AuthMiddlewareStack
            # Or, require login before chat connection.
            # We could also use a guest_identifier from the client.
            sender_email = "Guest"
            sender_is_staff = False
        else:
            sender_email = self.user.email
            sender_is_staff = self.user.is_staff

        # Save message to database
        msg_obj = await database_sync_to_async(ChatMessage.objects.create)(
            session=self.chat_session,
            sender=self.user if self.user.is_authenticated else None,
            message=message_text
        )

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message', # This will call the chat_message method below
                'message': message_text,
                'sender_email': sender_email,
                'sender_is_staff': sender_is_staff,
                'timestamp': msg_obj.timestamp.isoformat(),
            }
        )

    # Receive message from room group (this method is called by group_send)
    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'chat_message', # client-side type to distinguish messages
            'message': event['message'],
            'sender_email': event['sender_email'],
            'sender_is_staff': event['sender_is_staff'],
            'timestamp': event['timestamp'],
        }))

    async def send_system_message(self, message_text):
        # Create system message in DB (optional, or handle differently)
        # msg_obj = await database_sync_to_async(ChatMessage.objects.create)(
        #     session=self.chat_session,
        #     sender=None, # System message
        #     message=message_text,
        # )
        # Send system message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'system_message', # This will call the system_message method below
                'message': message_text,
                'timestamp': timezone.now().isoformat(),
            }
        )
    
    async def system_message(self, event):
        # Send system message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'system_message',
            'message': event['message'],
            'timestamp': event['timestamp'],
        })) 