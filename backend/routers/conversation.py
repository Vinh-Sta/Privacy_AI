from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, schemas, oauth2
from typing import List

router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"]
)

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.ConversationOut)
async def create_conversation(conversation: schemas.ConversationCreate, db: Session = Depends(get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    new_conversation = models.Conversation(**conversation.model_dump(), user_id=current_user.id)
    db.add(new_conversation)
    db.commit()
    db.refresh(new_conversation)

    return new_conversation

@router.get("/", response_model=List[schemas.ConversationOut])
async def get_conversations(db: Session = Depends(get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    conversations = db.query(models.Conversation).filter(models.Conversation.user_id == current_user.id).all()
    return conversations


@router.delete("/{conv_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(conv_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    conv = db.query(models.Conversation).filter(
        models.Conversation.id == conv_id,
        models.Conversation.user_id == current_user.id
    ).first()

    if not conv:
        raise HTTPException(status_code=404, detail="Can not find any conversations")

    db.delete(conv)
    db.commit()
    return None 