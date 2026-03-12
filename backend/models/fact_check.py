from sqlalchemy import Column, String, Integer, DateTime, JSON, Float
import datetime
from db.database import Base

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
