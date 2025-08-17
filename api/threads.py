from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from core.database import get_db
from core.websocket import manager
from services.auth import get_current_user
from models import User, Channel, ChannelMember, Message, Thread
from llm.llm_handler import llm_handler

router = APIRouter()


class ThreadCreate(BaseModel):
    channel_id: UUID
    root_message_id: UUID
    title: Optional[str] = None
    is_llm_enabled: bool = True
    allowed_databases: Optional[List[str]] = None
    allowed_tables: Optional[List[str]] = None


class ThreadResponse(BaseModel):
    id: str
    channel_id: str
    root_message_id: str
    title: Optional[str]
    is_llm_enabled: bool
    message_count: int
    participant_count: int
    created_at: str
    allowed_databases: Optional[List[str]]
    allowed_tables: Optional[List[str]]
    
    class Config:
        from_attributes = True


class LLMQueryRequest(BaseModel):
    thread_id: UUID
    query: str
    context: Optional[Dict[str, Any]] = None


@router.post("/", response_model=ThreadResponse)
async def create_thread(
    thread_data: ThreadCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify user has access to channel
    result = await db.execute(
        select(ChannelMember)
        .where(and_(
            ChannelMember.channel_id == thread_data.channel_id,
            ChannelMember.user_id == current_user.id
        ))
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not a member of this channel")
    
    # Create thread
    thread = Thread(
        channel_id=thread_data.channel_id,
        root_message_id=thread_data.root_message_id,
        title=thread_data.title,
        is_llm_enabled=thread_data.is_llm_enabled,
        allowed_databases=thread_data.allowed_databases,
        allowed_tables=thread_data.allowed_tables,
        participant_count=1,
        message_count=0
    )
    
    db.add(thread)
    await db.commit()
    await db.refresh(thread)
    
    return ThreadResponse(
        id=str(thread.id),
        channel_id=str(thread.channel_id),
        root_message_id=str(thread.root_message_id),
        title=thread.title,
        is_llm_enabled=thread.is_llm_enabled,
        message_count=thread.message_count,
        participant_count=thread.participant_count,
        created_at=thread.created_at.isoformat(),
        allowed_databases=thread.allowed_databases,
        allowed_tables=thread.allowed_tables
    )


@router.post("/{thread_id}/llm-query")
async def execute_llm_query(
    thread_id: UUID,
    query_request: LLMQueryRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Get thread
    result = await db.execute(select(Thread).where(Thread.id == thread_id))
    thread = result.scalar_one_or_none()
    
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    if not thread.is_llm_enabled:
        raise HTTPException(status_code=400, detail="LLM is not enabled for this thread")
    
    # Verify user has access to channel
    result = await db.execute(
        select(ChannelMember)
        .where(and_(
            ChannelMember.channel_id == thread.channel_id,
            ChannelMember.user_id == current_user.id
        ))
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not a member of this channel")
    
    # Create user message
    user_message = Message(
        channel_id=thread.channel_id,
        author_id=current_user.id,
        thread_id=thread_id,
        content=query_request.query,
        message_type="text"
    )
    db.add(user_message)
    await db.flush()
    
    # Process in background
    background_tasks.add_task(
        process_llm_query_task,
        thread_id=str(thread_id),
        channel_id=str(thread.channel_id),
        user_query=query_request.query,
        allowed_tables=thread.allowed_tables,
        context=query_request.context
    )
    
    await db.commit()
    
    return {
        "message": "Query submitted for processing",
        "user_message_id": str(user_message.id)
    }


async def process_llm_query_task(
    thread_id: str,
    channel_id: str,
    user_query: str,
    allowed_tables: Optional[List[str]],
    context: Optional[Dict[str, Any]]
):
    """Background task to process LLM query and send results via WebSocket."""
    
    # Process the data request
    result = await llm_handler.process_data_request(
        user_prompt=user_query,
        allowed_tables=allowed_tables,
        enterprise_context=context
    )
    
    # Create LLM response message
    from core.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db:
        llm_message = Message(
            channel_id=UUID(channel_id),
            author_id=UUID("00000000-0000-0000-0000-000000000000"),  # System user
            thread_id=UUID(thread_id),
            content=result.get("formatted_results", result.get("message", "Error processing query")),
            message_type="llm_response",
            llm_context={
                "query": user_query,
                "sql_query": result.get("sql_query"),
                "row_count": result.get("row_count"),
                "success": result.get("success"),
                "error": result.get("error")
            },
            llm_model_used=result.get("model_used")
        )
        
        db.add(llm_message)
        await db.commit()
        
        # Broadcast via WebSocket
        await manager.broadcast_to_channel(
            {
                "type": "llm_response",
                "thread_id": thread_id,
                "message": {
                    "id": str(llm_message.id),
                    "content": llm_message.content,
                    "llm_context": llm_message.llm_context,
                    "created_at": llm_message.created_at.isoformat()
                }
            },
            channel_id
        )


@router.get("/{thread_id}/messages", response_model=List[Dict[str, Any]])
async def get_thread_messages(
    thread_id: UUID,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Get thread
    result = await db.execute(select(Thread).where(Thread.id == thread_id))
    thread = result.scalar_one_or_none()
    
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    # Verify user has access
    result = await db.execute(
        select(ChannelMember)
        .where(and_(
            ChannelMember.channel_id == thread.channel_id,
            ChannelMember.user_id == current_user.id
        ))
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not a member of this channel")
    
    # Get messages
    result = await db.execute(
        select(Message, User)
        .join(User, Message.author_id == User.id, isouter=True)
        .where(Message.thread_id == thread_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    
    messages = result.all()
    
    return [
        {
            "id": str(message.id),
            "author_id": str(message.author_id),
            "author_username": user.username if user else "System",
            "content": message.content,
            "message_type": message.message_type,
            "llm_context": message.llm_context,
            "created_at": message.created_at.isoformat()
        }
        for message, user in messages
    ][::-1]