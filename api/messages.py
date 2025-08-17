from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from core.database import get_db
from core.websocket import manager
from services.auth import get_current_user
from models import User, Channel, ChannelMember, Message, Thread

router = APIRouter()


class MessageCreate(BaseModel):
    channel_id: UUID
    content: str
    thread_id: Optional[UUID] = None
    parent_message_id: Optional[UUID] = None
    mentions: Optional[List[str]] = None


class MessageResponse(BaseModel):
    id: str
    channel_id: str
    author_id: str
    author_username: str
    content: str
    message_type: str
    thread_id: Optional[str]
    parent_message_id: Optional[str]
    is_edited: bool
    created_at: str
    mentions: Optional[List[str]]
    
    class Config:
        from_attributes = True


@router.post("/", response_model=MessageResponse)
async def send_message(
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify user is member of channel
    result = await db.execute(
        select(ChannelMember)
        .where(and_(
            ChannelMember.channel_id == message_data.channel_id,
            ChannelMember.user_id == current_user.id
        ))
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not a member of this channel")
    
    # Create message
    message = Message(
        channel_id=message_data.channel_id,
        author_id=current_user.id,
        content=message_data.content,
        thread_id=message_data.thread_id,
        parent_message_id=message_data.parent_message_id,
        mentions=message_data.mentions,
        message_type="text"
    )
    
    db.add(message)
    await db.commit()
    await db.refresh(message)
    
    # Prepare response
    response = MessageResponse(
        id=str(message.id),
        channel_id=str(message.channel_id),
        author_id=str(message.author_id),
        author_username=current_user.username,
        content=message.content,
        message_type=message.message_type,
        thread_id=str(message.thread_id) if message.thread_id else None,
        parent_message_id=str(message.parent_message_id) if message.parent_message_id else None,
        is_edited=message.is_edited,
        created_at=message.created_at.isoformat(),
        mentions=message.mentions
    )
    
    # Broadcast to channel via WebSocket
    await manager.broadcast_to_channel(
        {
            "type": "new_message",
            "message": response.dict()
        },
        str(message_data.channel_id)
    )
    
    return response


@router.get("/channel/{channel_id}", response_model=List[MessageResponse])
async def get_channel_messages(
    channel_id: UUID,
    limit: int = 50,
    before: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify user is member of channel
    result = await db.execute(
        select(ChannelMember)
        .where(and_(
            ChannelMember.channel_id == channel_id,
            ChannelMember.user_id == current_user.id
        ))
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not a member of this channel")
    
    # Build query
    query = select(Message, User).join(User).where(
        Message.channel_id == channel_id
    )
    
    if before:
        query = query.where(Message.created_at < before)
    
    query = query.order_by(Message.created_at.desc()).limit(limit)
    
    result = await db.execute(query)
    messages = result.all()
    
    return [
        MessageResponse(
            id=str(message.id),
            channel_id=str(message.channel_id),
            author_id=str(message.author_id),
            author_username=user.username,
            content=message.content,
            message_type=message.message_type,
            thread_id=str(message.thread_id) if message.thread_id else None,
            parent_message_id=str(message.parent_message_id) if message.parent_message_id else None,
            is_edited=message.is_edited,
            created_at=message.created_at.isoformat(),
            mentions=message.mentions
        )
        for message, user in messages
    ][::-1]  # Reverse to get chronological order