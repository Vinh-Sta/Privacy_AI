from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List


class UserOut(BaseModel):
    email: EmailStr
    created_at: datetime
    
    # convert SQLAlchemy model to pydantic model
    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: Optional[int] = None


class MessageBase(BaseModel):
    role: str #'user' or 'assistant'
    content: str

class MessageCreate(MessageBase):
    pass

class MessageOut(MessageBase):
    id: int
    conversation_id: int
    timestamp: datetime

    class Config:
        from_attributes = True

#Schemas cho Attachment (Attachmentfile - support for RAG)
class AttachmentOut(BaseModel):
    id: int
    file_name: str
    upload_at: datetime

    class Config:
        from_attributes = True

# 3. Schemas for Conversation
class ConversationBase(BaseModel):
    title: Optional[str] = "New Conversation"

class ConversationCreate(ConversationBase):
    pass

class ConversationOut(ConversationBase):
    id: int
    user_id: int
    updated_at: datetime
    
    messages: List[MessageOut] = []
    attachments: List[AttachmentOut] = []

    class Config:
        from_attributes = True
