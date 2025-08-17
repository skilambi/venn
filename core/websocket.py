from typing import Dict, Set, List
from fastapi import WebSocket
import json
import asyncio
from datetime import datetime
import uuid


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_channels: Dict[str, Set[str]] = {}
        self.channel_users: Dict[str, Set[str]] = {}
        
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        
    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            
        # Remove user from all channels
        if user_id in self.user_channels:
            for channel_id in self.user_channels[user_id]:
                if channel_id in self.channel_users:
                    self.channel_users[channel_id].discard(user_id)
            del self.user_channels[user_id]
    
    def add_user_to_channel(self, user_id: str, channel_id: str):
        if user_id not in self.user_channels:
            self.user_channels[user_id] = set()
        self.user_channels[user_id].add(channel_id)
        
        if channel_id not in self.channel_users:
            self.channel_users[channel_id] = set()
        self.channel_users[channel_id].add(user_id)
    
    def remove_user_from_channel(self, user_id: str, channel_id: str):
        if user_id in self.user_channels:
            self.user_channels[user_id].discard(channel_id)
        if channel_id in self.channel_users:
            self.channel_users[channel_id].discard(user_id)
    
    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            await websocket.send_json(message)
    
    async def broadcast_to_channel(self, message: dict, channel_id: str, exclude_user: str = None):
        if channel_id in self.channel_users:
            tasks = []
            for user_id in self.channel_users[channel_id]:
                if user_id != exclude_user and user_id in self.active_connections:
                    websocket = self.active_connections[user_id]
                    tasks.append(websocket.send_json(message))
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
    
    async def broadcast_typing_indicator(self, channel_id: str, user_id: str, is_typing: bool):
        message = {
            "type": "typing_indicator",
            "channel_id": channel_id,
            "user_id": user_id,
            "is_typing": is_typing,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast_to_channel(message, channel_id, exclude_user=user_id)
    
    async def notify_user_status(self, user_id: str, status: str):
        message = {
            "type": "user_status",
            "user_id": user_id,
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Notify all channels the user is in
        if user_id in self.user_channels:
            for channel_id in self.user_channels[user_id]:
                await self.broadcast_to_channel(message, channel_id)


manager = ConnectionManager()