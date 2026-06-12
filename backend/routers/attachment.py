from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from typing import cast
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, schemas, oauth2
import os
import time
import shutil
from ..services.file_handler import save_uploaded_file, create_attachment_record
from ..services.rag_service import process_and_store_pdf

router = APIRouter(
    prefix="/conversations/{conv_id}/attachments",
    tags=["Attachments"]
)

current_dir = os.path.dirname(os.path.abspath(__file__))

# 2. Lùi lại 1 cấp để ra thư mục 'backend', rồi nối thêm chữ 'uploads'
UPLOAD_DIR = os.path.join(os.path.dirname(current_dir), "uploads")

# 3. Tạo thư mục nếu chưa có
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/", response_model=schemas.AttachmentOut, status_code=status.HTTP_201_CREATED)
def upload_file(
    conv_id: int, 
    file: UploadFile = File(...), 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(oauth2.get_current_user),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    # 1. Kiểm tra quyền sở hữu cuộc trò chuyện
    conversation = db.query(models.Conversation).filter(
        models.Conversation.id == conv_id,
        models.Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy cuộc trò chuyện")
    
    # # 2. Kiểm tra định dạng file (chỉ cho phép PDF)
    # if not file.filename or not file.filename.lower().endswith('.pdf'):
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Hệ thống hiện chỉ hỗ trợ file PDF.")

    # # 3. Tạo tên file độc nhất và lưu vào thư mục 'uploads'
    # safe_filename = f"{int(time.time())}_{file.filename}"
    # file_path = os.path.join(UPLOAD_DIR, safe_filename)

    # try:
    #     # shutil.copyfileobj giúp lưu file lớn mà không bị tràn RAM
    #     with open(file_path, "wb") as buffer:
    #         shutil.copyfileobj(file.file, buffer)
    # except Exception as e:
    #     raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Lỗi khi lưu file: {str(e)}")
    # finally:
    #     file.file.close() # Đóng luồng file để giải phóng tài nguyên

    # # 4. Lưu thông tin vào Database (Bảng Attachments)
    # new_attachment = models.Attachment(
    #     conversation_id=conv_id,
    #     file_name=file.filename,
    #     file_path=file_path
    # )
    
    # db.add(new_attachment)
    # db.commit()
    # db.refresh(new_attachment)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            

    # attachement_id = cast(int, new_attachment.id)

    file_path = save_uploaded_file(file, UPLOAD_DIR)
    new_attachment = create_attachment_record(db, conv_id, str(file.filename), file_path)

    attachement_id = cast(int, new_attachment.id)
    background_tasks.add_task(
        process_and_store_pdf, 
        file_path=file_path, 
        conversation_id=conv_id, 
        attachment_id= attachement_id,
    )

    return new_attachment

@router.get("/", response_model=list[schemas.AttachmentOut])
def get_attachments(
    conv_id: int, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(oauth2.get_current_user)
):
    # 1. Kiểm tra quyền sở hữu
    conversation = db.query(models.Conversation).filter(
        models.Conversation.id == conv_id,
        models.Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy cuộc trò chuyện")

    # 2. Lấy danh sách file
    attachments = db.query(models.Attachment).filter(models.Attachment.conversation_id == conv_id).all()
    return attachments

@router.get("/{attachment_id}/status")
def check_attachment_status(
    attachment_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    """API để Frontend gọi định kỳ kiểm tra trạng thái file"""
    attachment = db.query(models.Attachment).filter(models.Attachment.id == attachment_id).first()
    
    if not attachment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy file")
        
    return {"id": attachment.id, "status": attachment.status}