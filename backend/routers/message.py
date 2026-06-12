from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, schemas, oauth2
from typing import List
from ..services.ai_bot import AIChatBot
from datetime import datetime, timezone

router = APIRouter(
    prefix="/conversations/{conv_id}/messages",
    tags=["Messages"]
)

ai_service = AIChatBot()

@router.post("/", response_model=schemas.MessageOut)
def send_message(conv_id: int, message_data: schemas.MessageCreate, db: Session = Depends(get_db), current_user: models.User = Depends(oauth2.get_current_user) ):
    # Check if conversation exists and belongs to current user
    conversation = db.query(models.Conversation).filter(models.Conversation.id == conv_id, models.Conversation.user_id == current_user.id).first()
    
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    
    past_messages = db.query(models.Message).filter(models.Message.conversation_id == conv_id).order_by(models.Message.timestamp.asc()).all()
    
    attachment_count = db.query(models.Attachment).filter(models.Attachment.conversation_id == conv_id).count()
    has_attachments = attachment_count > 0 
    # Response from AI Bot
    try:
        ai_response_content = ai_service.get_response(
            past_messages=past_messages, 
            new_content=message_data.content, 
            conv_id=conv_id, 
            has_attachments=has_attachments
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    # Lưu cả 2 tin nhắn user và AI vào Database
    user_msg = models.Message(conversation_id=conv_id, role="user", content=message_data.content)
    ai_msg = models.Message(conversation_id=conv_id, role="assistant", content=ai_response_content)
    
    db.add(user_msg)
    db.add(ai_msg)
    
    # Update time for Conversation
    setattr(conversation, "updated_at", datetime.now(timezone.utc))
    
    db.commit()
    db.refresh(ai_msg)

    return ai_msg

@router.get("/", response_model=List[schemas.MessageOut])
def get_messages(
    conv_id: int, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(oauth2.get_current_user)
):
    # Lấy lịch sử chat của một cuộc hội thoại cụ thể
    messages = db.query(models.Message).filter(models.Message.conversation_id == conv_id).all()
    return messages

