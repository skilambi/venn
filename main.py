from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import json
from typing import Optional

from config.settings import get_settings
from core.database import init_db
from core.websocket import manager
from api import auth, users, channels, messages, threads
from services.auth import get_current_user_ws

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown
    # Add any cleanup code here


app = FastAPI(
    title=settings.app_name,
    version=settings.api_version,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix=f"/api/{settings.api_version}/auth", tags=["auth"])
app.include_router(users.router, prefix=f"/api/{settings.api_version}/users", tags=["users"])
app.include_router(channels.router, prefix=f"/api/{settings.api_version}/channels", tags=["channels"])
app.include_router(messages.router, prefix=f"/api/{settings.api_version}/messages", tags=["messages"])
app.include_router(threads.router, prefix=f"/api/{settings.api_version}/threads", tags=["threads"])


@app.get("/")
async def root():
    return {"message": "Chat Server API", "version": settings.api_version}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    user = await get_current_user_ws(token)
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    user_id = str(user.id)
    await manager.connect(websocket, user_id)
    await manager.notify_user_status(user_id, "online")
    
    try:
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            if message_type == "join_channel":
                channel_id = data.get("channel_id")
                manager.add_user_to_channel(user_id, channel_id)
                await manager.send_personal_message({
                    "type": "channel_joined",
                    "channel_id": channel_id
                }, user_id)
                
            elif message_type == "leave_channel":
                channel_id = data.get("channel_id")
                manager.remove_user_from_channel(user_id, channel_id)
                await manager.send_personal_message({
                    "type": "channel_left",
                    "channel_id": channel_id
                }, user_id)
                
            elif message_type == "typing":
                channel_id = data.get("channel_id")
                is_typing = data.get("is_typing", False)
                await manager.broadcast_typing_indicator(channel_id, user_id, is_typing)
                
            elif message_type == "ping":
                await manager.send_personal_message({"type": "pong"}, user_id)
                
    except WebSocketDisconnect:
        manager.disconnect(user_id)
        await manager.notify_user_status(user_id, "offline")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.debug
    )