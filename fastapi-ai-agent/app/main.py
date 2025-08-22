import os
import io
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import uvicorn
from fastapi.middleware.cors import CORSMiddleware # Import CORSMiddleware

from app.core.config import S3_BUCKET_NAME, S3_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, GOOGLE_API_KEY 
from app.services.s3_service import S3Service
from app.db.database import engine
from app.models.file_metadata import Base
from app.api.v1 import file_upload, generation
from agents.chains import RAGChain, GeneratorChain

Base.metadata.create_all(bind=engine)
app = FastAPI()

# Configure CORS
origins = [
    "*" 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(file_upload.router, prefix="/api/v1", tags=["file_upload"])
app.include_router(generation.router, prefix="/api/v1", tags=["generation"])

s3_service = S3Service()
rag_chain = RAGChain()
generator_chain = None 

# --- Templates for HTML ---
templates = Jinja2Templates(directory="app/templates")

# --- Root Endpoint for Testing ---
@app.get("/", response_class=HTMLResponse)
async def main(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=True)
