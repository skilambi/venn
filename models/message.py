from sqlalchemy import Column, String, Text, ForeignKey, Boolean, Integer, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import BaseModel


class Message(BaseModel):
    __tablename__ = "messages"
    
    channel_id = Column(UUID(as_uuid=True), ForeignKey("channels.id"), nullable=False)
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    thread_id = Column(UUID(as_uuid=True), ForeignKey("threads.id"))
    parent_message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"))
    
    content = Column(Text, nullable=False)
    message_type = Column(String(50), default="text")  # text, llm_response, system, file
    is_edited = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    
    # For LLM responses
    llm_context = Column(JSON)  # Store query context, database info, etc.
    llm_model_used = Column(String(100))
    
    # Attachments and metadata
    attachments = Column(JSON)  # List of attachment objects
    reactions = Column(JSON)  # User reactions
    mentions = Column(JSON)  # Mentioned user IDs
    
    # Relationships
    channel = relationship("Channel", back_populates="messages")
    author = relationship("User", back_populates="messages")
    thread = relationship("Thread", back_populates="messages", foreign_keys=[thread_id])
    replies = relationship("Message", backref="parent", remote_side="Message.id")


class Thread(BaseModel):
    __tablename__ = "threads"
    
    channel_id = Column(UUID(as_uuid=True), ForeignKey("channels.id"), nullable=False)
    root_message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"))
    
    title = Column(String(255))
    is_llm_enabled = Column(Boolean, default=True)
    llm_context = Column(JSON)  # Store thread-specific LLM context
    participant_count = Column(Integer, default=0)
    message_count = Column(Integer, default=0)
    
    # Enterprise context
    allowed_databases = Column(JSON)  # List of allowed database connections
    allowed_tables = Column(JSON)  # List of allowed tables/views
    
    # Relationships
    messages = relationship("Message", back_populates="thread", foreign_keys="Message.thread_id", cascade="all, delete-orphan")