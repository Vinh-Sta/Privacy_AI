from .. import models, schemas
from fastapi import APIRouter, Depends, HTTPException, status, Response, APIRouter
from typing import List, Optional
from sqlalchemy.orm import Session
from ..database import get_db
from .. import utilis, models, utilis, oauth2




router = APIRouter(
    prefix="/users",
    tags=["Users"]
)




@router.post("/", status_code = status.HTTP_201_CREATED, response_model= schemas.UserOut)
async def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    
    # hash the password - user.passwird
    hashed_password = utilis.hash_password(user.password)
    user.password = hashed_password
    new_user = models.User(**user.model_dump())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.get("/{id}", response_model=schemas.UserOut)
async def get_user(id: int, db: Session = Depends(get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    user = db.query(models.User).filter(models.User.id == id).first()

    if not user:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND,
                            detail=f"user with id: {id} was not found")
    return user