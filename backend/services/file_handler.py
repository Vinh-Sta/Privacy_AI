import os
import time
import shutil
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from .. import models

def save_uploaded_file(file: UploadFile, upload_dir: str) -> str:
    """Lưu file vật lý xuống ổ cứng"""
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="System just supports PDF files.")

    safe_filename = f"{int(time.time())}_{file.filename}"
    file_path = os.path.join(upload_dir, safe_filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error saving file: {str(e)}")
    finally:
        file.file.close()
        
    return file_path

def create_attachment_record(db: Session, conv_id: int, filename: str, file_path: str) -> models.Attachment:
    """Tạo record trong Database với status mặc định là 'Processing'"""
    new_attachment = models.Attachment(
        conversation_id=conv_id,
        file_name=filename,
        file_path=file_path,
        status="Processing" # Trạng thái ban đầu
    )
    db.add(new_attachment)
    db.commit()
    db.refresh(new_attachment)
    return new_attachment