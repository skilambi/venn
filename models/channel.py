from sqlalchemy import Column, String, Boolean, Text, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import BaseModel


class Channel(BaseModel):
    __tablename__ = "channels"
    
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    is_private = Column(Boolean, default=False)
    is_direct_message = Column(Boolean, default=False)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    topic = Column(Text)
    
    # Relationships
    owner = relationship("User", back_populates="owned_channels")
    messages = relationship("Message", back_populates="channel", cascade="all, delete-orphan")
    members = relationship("ChannelMember", back_populates="channel", cascade="all, delete-orphan")


class ChannelMember(BaseModel):
    __tablename__ = "channel_members"
    
    channel_id = Column(UUID(as_uuid=True), ForeignKey("channels.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role = Column(String(50), default="member")  # owner, admin, member
    last_read_message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"))
    notification_level = Column(String(50), default="all")  # all, mentions, none
    
    # Relationships
    channel = relationship("Channel", back_populates="members")
    user = relationship("User", back_populates="channel_memberships")