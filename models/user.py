from sqlalchemy import Column, String, Boolean, Text
from sqlalchemy.orm import relationship
from .base import BaseModel


class User(BaseModel):
    __tablename__ = "users"
    
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(255))
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    avatar_url = Column(Text)
    status = Column(String(50), default="offline")  # online, offline, away, busy
    
    # Relationships
    messages = relationship("Message", back_populates="author", cascade="all, delete-orphan")
    channel_memberships = relationship("ChannelMember", back_populates="user", cascade="all, delete-orphan")
    owned_channels = relationship("Channel", back_populates="owner")