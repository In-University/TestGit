from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, validator # Import validator

class FileMetadataBase(BaseModel):
    file_name: str
    file_type: str
    language: Optional[str] = None # Make optional
    file_size_kb: int # Renamed and changed to int
    tags_part: Optional[List[str]] = None # Make optional
    status: Optional[str] = "Indexed"
    s3_url: str # Add S3 URL to schema
    user_id: int # Add user_id

class FileMetadataCreate(FileMetadataBase):
    pass

class FileMetadata(FileMetadataBase):
    id: int
    upload_timestamp: datetime
    s3_url: str # Add S3 URL to response schema
    user_id: int # Add user_id to response schema

    @validator('tags_part', pre=True, always=True)
    def parse_tags_part(cls, v):
        if isinstance(v, str):
            return [tag.strip() for tag in v.split(',') if tag.strip()]
        return v

    class Config:
        from_attributes = True
