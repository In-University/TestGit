from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import io
import os # Import os for file operations

from ...models.file_metadata import FileMetadata as DBFileMetadata
from ...schemas.file_metadata import FileMetadata 
from ...db.database import get_db
from ...services.s3_service import S3Service
from agents.chains import RAGChain

router = APIRouter()

s3_service = S3Service()
rag_chain = RAGChain() # Initialize RAGChain here

@router.post("/uploadfile/", response_model=FileMetadata)
async def create_upload_file(
    file: UploadFile = File(...),
    user_id: int = Form(...), 
    language: Optional[str] = None, 
    tags_part: Optional[List[str]] = None, 
    db: Session = Depends(get_db)
):

    file_name = file.filename
    file_type = file.content_type
    file_content = await file.read()
    file_size_bytes = len(file_content)
    file_size_kb = int(file_size_bytes / 1024) 

    file_like_object = io.BytesIO(file_content)
    try:
        s3_url = s3_service.upload_file(file_like_object, file.filename, file.content_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"S3 upload failed: {e}")

    # Save file locally for processing
    temp_file_path = f"/tmp/{file.filename}"
    with open(temp_file_path, "wb") as buffer:
        buffer.write(file_content)

    db_file_metadata = DBFileMetadata(
        file_name=file_name,
        file_type=file_type,
        language=language,
        file_size_kb=file_size_kb, 
        tags_part=",".join(tags_part) if tags_part else "", 
        status="Pending", # Set status to pending until RAG processing is complete
        s3_url=s3_url, 
        user_id=user_id 
    )
    db.add(db_file_metadata)
    try:
        db.commit()
        db.refresh(db_file_metadata)
        print(f"Successfully saved metadata for file: {db_file_metadata.file_name} with ID: {db_file_metadata.id}")
    except Exception as e:
        db.rollback()
        print(f"Database commit failed: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    if not rag_chain.process_document(temp_file_path, file.content_type, user_id, db_file_metadata.id):
        os.remove(temp_file_path)
        db_file_metadata.status = "Failed"
        db.add(db_file_metadata)
        db.commit()
        raise HTTPException(status_code=500, detail="Failed to process document for RAG.")
    
    db_file_metadata.status = "Indexed"
    db.add(db_file_metadata)
    db.commit()

    os.remove(temp_file_path)

    return db_file_metadata

@router.get("/{user_id}/files", response_model=List[FileMetadata])
async def get_user_files(user_id: int, db: Session = Depends(get_db)):
    files = db.query(DBFileMetadata).filter(DBFileMetadata.user_id == user_id).all()
    return files 
