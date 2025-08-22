from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from app.models.file_metadata import FileMetadata

SQLALCHEMY_DATABASE_URL = "mysql+mysqlconnector://root:Nguyenhuyhoang%401995%23@157.20.83.145/echo_english"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_file_metadata_by_ids(db: Session, file_ids: list[int], user_id: int):
    return db.query(FileMetadata).filter(
        FileMetadata.id.in_(file_ids),
        FileMetadata.user_id == user_id
    ).all()
