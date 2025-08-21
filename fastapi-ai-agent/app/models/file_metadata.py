from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from ..db.base import Base

class FileMetadata(Base):
    __tablename__ = "file_metadata"

    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String(255), index=True)
    file_type = Column(String(255))
    language = Column(String(255))
    file_size_kb = Column(Integer) # Storing as integer in KB
    tags_part = Column(String(255)) # Storing as comma-separated string for array-like data
    status = Column(String(255), default="Đã lập chỉ mục")
    s3_url = Column(String(512), nullable=False) # Add S3 URL column
    user_id = Column(Integer, nullable=False) # Add user_id column
    upload_timestamp = Column(DateTime, default=func.now())
