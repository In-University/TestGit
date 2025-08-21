import os
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import uvicorn

from .config import S3_BUCKET_NAME, S3_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, GOOGLE_API_KEY
from .services.s3_service import S3Service
from .services.rag_service import RAGService
from .services.generator_service import GeneratorService

# --- Initialize FastAPI App ---
app = FastAPI()

# --- Initialize Services ---
s3_service = S3Service()
rag_service = RAGService()
generator_service = None # Will be initialized after document processing

# --- Templates for HTML ---
templates = Jinja2Templates(directory="templates")

# --- API Endpoints ---
@app.post("/upload-and-process/")
async def upload_and_process_file(file: UploadFile = File(...)):
    """
    Handles file upload to S3 and processing for RAG.
    """
    # 1. Upload to S3
    try:
        s3_url = s3_service.upload_file(file.file, file.filename, file.content_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"S3 upload failed: {e}")

    # 2. Save file locally for processing
    temp_file_path = f"/tmp/{file.filename}"
    with open(temp_file_path, "wb") as buffer:
        buffer.write(await file.read())

    # 3. Process the document for RAG
    if not rag_service.process_document(temp_file_path, file.content_type):
        raise HTTPException(status_code=500, detail="Failed to process document for RAG.")
        
    # Initialize generator service after RAG chain is ready
    global generator_service
    generator_service = GeneratorService(rag_service.get_qa_chain())

    # Clean up the temporary file
    os.remove(temp_file_path)

    return {
        "message": "File uploaded and processed successfully.",
        "s3_url": s3_url
    }

@app.post("/generate/flashcards/")
async def generate_flashcards(topic: str = Form(...)):
    """
    Generates flashcards based on the processed document.
    """
    if not generator_service:
        raise HTTPException(status_code=400, detail="No document processed yet. Please upload a file first.")
    
    try:
        flashcards = generator_service.generate_flashcards(topic)
        return {"flashcards": flashcards}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate flashcards: {e}")


@app.post("/generate/quiz/")
async def generate_quiz(part: int = Form(...)):
    """
    Generates a TOEIC-style quiz for a specific part.
    """
    if not generator_service:
        raise HTTPException(status_code=400, detail="No document processed yet. Please upload a file first.")

    try:
        quiz = generator_service.generate_quiz(part)
        return {"quiz": quiz}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate quiz: {e}")

# --- Root Endpoint for Testing ---
@app.get("/", response_class=HTMLResponse)
async def main(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# --- To run the app ---
# uvicorn app:app --reload
