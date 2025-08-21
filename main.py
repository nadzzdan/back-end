import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Read from .env
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# MySQL connection string (no SQLite fallback)
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# SQLAlchemy setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# DB model
class TextEntry(Base):
    __tablename__ = "entries"
    id = Column(Integer, primary_key=True, index=True)
    content = Column(String(255), nullable=False)

# Create table (once)
Base.metadata.create_all(bind=engine)

# Pydantic schemas
class EntryIn(BaseModel):
    content: str

class EntryOut(BaseModel):
    id: int
    content: str

    class Config:
        orm_mode = True

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# FastAPI app
app = FastAPI()

# CORS config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
@app.post("/entries/", response_model=EntryOut)
def create_entry(entry: EntryIn, db: Session = Depends(get_db)):
    db_entry = TextEntry(content=entry.content)
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return db_entry

@app.get("/entries/", response_model=list[EntryOut])
def read_entries(db: Session = Depends(get_db)):
    return db.query(TextEntry).all()
