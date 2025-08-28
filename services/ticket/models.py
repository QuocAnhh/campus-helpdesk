from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SQLEnum, ForeignKey, Index
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime
import enum

class TicketStatus(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"

class TicketPriority(str, enum.Enum):
    low = "low"
    normal = "normal"
    high = "high"
    urgent = "urgent"

class TicketCategory(str, enum.Enum):
    technical = "technical"
    account = "account"
    general = "general"
    academic = "academic"
    facility = "facility"

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String(255), nullable=False, index=True)
    content = Column(Text, nullable=False)
    category = Column(SQLEnum(TicketCategory), default=TicketCategory.general)
    priority = Column(SQLEnum(TicketPriority), default=TicketPriority.normal)
    status = Column(SQLEnum(TicketStatus), default=TicketStatus.open)
    
    # User information
    user_id = Column(Integer, nullable=False)  # Reference to user who created the ticket
    user_name = Column(String(255), nullable=False)  # Store username for easy access
    user_email = Column(String(255), nullable=False)  # Store email for notifications
    student_id = Column(String(50), nullable=True, index=True)  # Student ID for identification
    
    # Assignment
    assigned_to = Column(String(255), nullable=True)  # Admin/agent assigned to this ticket
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    
    # Additional info
    resolution = Column(Text, nullable=True)  # Resolution details when ticket is resolved 

    # Indexes
    __table_args__ = (
        Index('ix_ticket_student_status', 'student_id', 'status'),
    )