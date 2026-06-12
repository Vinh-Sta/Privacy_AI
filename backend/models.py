from .database import Base
from sqlalchemy.sql import func
from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, TIMESTAMP, Text, DateTime
import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Text

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key = True, nullable = False)
    email = Column(String, nullable = False, unique = True)
    password = Column(String, nullable = False)
    created_at = Column(TIMESTAMP(timezone = True), server_default = 'now()', nullable = False)
    
    # One-to-Many relationship: User to Conversations ----> để tìm hiểu thêm
    conversations = relationship("Conversation", back_populates="owner")

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, default="New Conversation")
    # auto update timestamp when Conversation is updated (Examples: add message, attachment)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    owner = relationship("User", back_populates="conversations")
    # One conversation contains Messages and Attachments (PDF)
    messages = relationship("Message", back_populates="parent_conversation", cascade="all, delete-orphan")
    attachments = relationship("Attachment", back_populates="parent_conversation", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    role = Column(String) # 'user' or 'assistant'
    content = Column(Text)
    timestamp = Column(DateTime(timezone=True), default=func.now())

    parent_conversation = relationship("Conversation", back_populates="messages")

class Attachment(Base):
    __tablename__ = "attachments"
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    file_name = Column(String)
    file_path = Column(String)  # path (e.g., ./uploads/file.pdf)
    # collection_name = Column(String) # Key to Milvus
    # file_content = Column(Text, nullable =True)
    status = Column(String, default= "Processing")
    upload_at = Column(DateTime(timezone=True), default=func.now())

    parent_conversation = relationship("Conversation", back_populates="attachments")