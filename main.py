import os
import time
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.exc import OperationalError
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
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# DB model
class TextEntry(Base):
    __tablename__ = "entries"
    id = Column(Integer, primary_key=True, index=True)
    content = Column(String(255), nullable=False)

# Function to initialize database with retry logic
def init_db(retries=5, delay=2):
    """Initialize database tables with retry logic"""
    for attempt in range(retries):
        try:
            Base.metadata.create_all(bind=engine)
            print(f"Database initialized successfully on attempt {attempt + 1}")
            return
        except OperationalError as e:
            if attempt < retries - 1:
                print(f"Database connection attempt {attempt + 1} failed. Retrying in {delay}s...")
                time.sleep(delay)
            else:
                print(f"Failed to connect to database after {retries} attempts")
                raise

# Pydantic schemas
class EntryIn(BaseModel):
    content: str

class EntryOut(BaseModel):
    id: int
    content: str

    class Config:
        from_attributes = True

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

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    init_db()

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
