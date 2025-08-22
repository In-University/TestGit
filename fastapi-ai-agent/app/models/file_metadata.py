from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from ..db.base import Base

class FileMetadata(Base):
    __tablename__ = "file_metadata"

    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String(255), index=True)
    file_type = Column(String(255))
    language = Column(String(255))
    file_size_kb = Column(Integer)
    tags_part = Column(String(255))
    status = Column(String(255), default="Đã lập chỉ mục")
    s3_url = Column(String(512), nullable=False)
    user_id = Column(Integer, nullable=False)
    upload_timestamp = Column(DateTime, default=func.now())
