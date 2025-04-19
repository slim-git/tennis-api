from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dotenv import load_dotenv
import os

load_dotenv()

def get_engine():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL is not set in environment variables")
    return create_engine(database_url)

def get_session() -> Generator:
    """
    Get a connection to the Postgres database
    """
    engine = get_engine()
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
