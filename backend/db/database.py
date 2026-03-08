from sqlalchemy import Column, String, Integer, DateTime, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./factchecker.db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class FactCheck(Base):
    __tablename__ = "fact_checks"
    
    id = Column(Integer, primary_key=True, index=True)
    whatsapp_id = Column(String, index=True)
    from_number = Column(String)
    claim = Column(String, index=True)
    transcript = Column(String)
    verdict = Column(String)
    confidence = Column(Float)
    virality_score = Column(Integer)
    explanation = Column(String)
    language = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    metadata_json = Column(JSON)
    counter_message = Column(String, default="")
    flagged_by_ngo = Column(Integer, default=0)

def init_db():
    Base.metadata.create_all(bind=engine)
