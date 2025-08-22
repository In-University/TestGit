from typing import List, Optional
from fastapi import APIRouter, Form, HTTPException, Depends
from sqlalchemy.orm import Session
from agents.chains import RAGChain, GeneratorChain
from app.db.database import get_db, get_file_metadata_by_ids
from app.models.file_metadata import FileMetadata

router = APIRouter()
rag_chain = RAGChain()

@router.post("/generate/flashcards/")
async def generate_flashcards(
    topic: str = Form(...),
    file_ids: List[int] = Form(...),
    user_id: int = Form(99),
    db: Session = Depends(get_db)
):
    """
    Generates flashcards based on specific processed documents for a specific user.
    """
    db_files: List[FileMetadata] = get_file_metadata_by_ids(db, file_ids, user_id)
    if not db_files or len(db_files) != len(file_ids):
        raise HTTPException(status_code=404, detail="One or more files not found or do not belong to the user.")
    
    qa_chain = rag_chain.get_qa_chain(user_id, file_ids)
    if not qa_chain:
        raise HTTPException(status_code=400, detail="No processed content found for the specified files for this user.")
    
    generator_chain = GeneratorChain(qa_chain)
    try:
        flashcards = generator_chain.generate_flashcards(topic)
        return {"flashcards": flashcards}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate flashcards: {e}")


@router.post("/generate/quiz/")
async def generate_quiz(
    part: int = Form(...),
    user_id: int = Form(99),
    file_ids: Optional[List[int]] = Form(None), 
    db: Session = Depends(get_db)
):
    """
    Generates a TOEIC-style quiz for a specific part for a specific user,
    optionally filtered by specific documents.
    """
    if file_ids:
        # Validate file ownership and existence if file_ids are provided
        db_files: List[FileMetadata] = get_file_metadata_by_ids(db, file_ids, user_id)
        if not db_files or len(db_files) != len(file_ids):
            raise HTTPException(status_code=404, detail="One or more files not found or do not belong to the user.")

    qa_chain = rag_chain.get_qa_chain(user_id, file_ids)
    if not qa_chain:
        detail_message = "No document processed yet for this user."
        if file_ids:
            detail_message = "No processed content found for the specified files for this user."
        raise HTTPException(status_code=400, detail=detail_message)

    generator_chain = GeneratorChain(qa_chain)
    try:
        quiz = generator_chain.generate_quiz(part)
        return {"quiz": quiz}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate quiz: {e}")

@router.post("/chat/")
async def chat_with_document(
    query: str = Form(...),
    user_id: int = Form(99),
    file_ids: Optional[List[int]] = Form(None), 
    db: Session = Depends(get_db)
):
    """
    Provides a chat interface to query the processed document for a specific user,
    optionally filtered by specific documents.
    """
    if file_ids:
        # Validate file ownership and existence if file_ids are provided
        db_files: List[FileMetadata] = get_file_metadata_by_ids(db, file_ids, user_id)
        if not db_files or len(db_files) != len(file_ids):
            raise HTTPException(status_code=404, detail="One or more files not found or do not belong to the user.")

    qa_chain = rag_chain.get_qa_chain(user_id, file_ids)
    if not qa_chain:
        detail_message = "No document processed yet for this user."
        if file_ids:
            detail_message = "No processed content found for the specified files for this user."
        raise HTTPException(status_code=400, detail=detail_message)
    
    try:
        result = qa_chain.run(query)
        return {"response": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to chat with document: {e}")
