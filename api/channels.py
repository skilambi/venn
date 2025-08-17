from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

from core.database import get_db
from services.auth import get_current_user
from models import User, Channel, ChannelMember

router = APIRouter()


class ChannelCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_private: bool = False


class ChannelResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    is_private: bool
    owner_id: str
    created_at: str
    
    class Config:
        from_attributes = True


@router.post("/", response_model=ChannelResponse)
async def create_channel(
    channel_data: ChannelCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    channel = Channel(
        name=channel_data.name,
        description=channel_data.description,
        is_private=channel_data.is_private,
        owner_id=current_user.id
    )
    
    db.add(channel)
    await db.flush()
    
    # Add creator as channel member
    member = ChannelMember(
        channel_id=channel.id,
        user_id=current_user.id,
        role="owner"
    )
    db.add(member)
    
    await db.commit()
    await db.refresh(channel)
    
    return ChannelResponse(
        id=str(channel.id),
        name=channel.name,
        description=channel.description,
        is_private=channel.is_private,
        owner_id=str(channel.owner_id),
        created_at=channel.created_at.isoformat()
    )


@router.get("/", response_model=List[ChannelResponse])
async def list_channels(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Get channels user is a member of
    result = await db.execute(
        select(Channel)
        .join(ChannelMember)
        .where(ChannelMember.user_id == current_user.id)
    )
    channels = result.scalars().all()
    
    return [
        ChannelResponse(
            id=str(channel.id),
            name=channel.name,
            description=channel.description,
            is_private=channel.is_private,
            owner_id=str(channel.owner_id),
            created_at=channel.created_at.isoformat()
        )
        for channel in channels
    ]


@router.post("/{channel_id}/join")
async def join_channel(
    channel_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Check if channel exists
    result = await db.execute(select(Channel).where(Channel.id == channel_id))
    channel = result.scalar_one_or_none()
    
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    # Check if already a member
    result = await db.execute(
        select(ChannelMember)
        .where(ChannelMember.channel_id == channel_id)
        .where(ChannelMember.user_id == current_user.id)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already a member of this channel")
    
    # Add as member
    member = ChannelMember(
        channel_id=channel_id,
        user_id=current_user.id,
        role="member"
    )
    db.add(member)
    await db.commit()
    
    return {"message": "Successfully joined channel"}