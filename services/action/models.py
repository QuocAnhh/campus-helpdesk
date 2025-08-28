# Action Requests Service - Database Schema

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()

class ActionRequest(Base):
    __tablename__ = "action_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(50), nullable=False, index=True)
    action_type = Column(String(50), nullable=False)
    status = Column(String(20), default="submitted")
    
    # Request data
    request_data = Column(JSON, nullable=False)  # Original form data
    
    # Processing info
    submitted_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    processed_by = Column(String(100), nullable=True)  # Admin user
    
    # Results
    result_data = Column(JSON, nullable=True)  # Response from action service
    external_id = Column(String(100), nullable=True)  # ticket_id, booking_id, etc.
    
    # Additional tracking
    client_ip = Column(String(50), nullable=True)
    user_agent = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)  # Admin notes
    
    def __repr__(self):
        return f"<ActionRequest(id={self.id}, student_id={self.student_id}, action_type={self.action_type}, status={self.status})>"

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://campus_user:campus_pass@mysql:3306/campus_helpdesk")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    Base.metadata.create_all(bind=engine)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
