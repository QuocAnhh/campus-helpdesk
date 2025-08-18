from sqlalchemy import Column, Integer, String, JSON, DateTime
from .database import Base
from datetime import datetime

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String(255), index=True)
    category = Column(String(100))
    priority = Column(String(50), default="normal")
    status = Column(String(50), default="open")
    created_at = Column(DateTime, default=datetime.utcnow)
    content = Column(JSON) 