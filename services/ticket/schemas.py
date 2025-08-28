from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from models import TicketStatus, TicketPriority, TicketCategory

# Base schemas
class TicketBase(BaseModel):
    subject: str = Field(..., min_length=5, max_length=255, description="Ticket subject")
    content: str = Field(..., min_length=10, description="Detailed description of the issue")
    category: TicketCategory = Field(default=TicketCategory.general, description="Ticket category")
    priority: TicketPriority = Field(default=TicketPriority.normal, description="Ticket priority")

# Request schemas
class TicketCreate(TicketBase):
    student_id: Optional[str] = Field(None, max_length=50, description="Student ID for identification")

class TicketUpdate(BaseModel):
    subject: Optional[str] = Field(None, min_length=5, max_length=255)
    content: Optional[str] = Field(None, min_length=10)
    category: Optional[TicketCategory] = None
    priority: Optional[TicketPriority] = None
    status: Optional[TicketStatus] = None
    assigned_to: Optional[str] = None
    resolution: Optional[str] = None
    student_id: Optional[str] = Field(None, max_length=50, description="Student ID for identification")

class TicketStatusUpdate(BaseModel):
    status: TicketStatus
    resolution: Optional[str] = None

# Response schemas
class TicketResponse(TicketBase):
    id: int
    status: TicketStatus
    user_id: int
    user_name: str
    user_email: str
    student_id: Optional[str] = None
    assigned_to: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    resolution: Optional[str] = None

    class Config:
        from_attributes = True

# Alias for TicketOut as requested  
TicketOut = TicketResponse

class TicketListResponse(BaseModel):
    id: int
    subject: str
    content: str  # Add content field for displaying description
    category: TicketCategory
    priority: TicketPriority
    status: TicketStatus
    user_name: str
    student_id: Optional[str] = None
    assigned_to: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Pagination and filtering
class TicketFilter(BaseModel):
    status: Optional[TicketStatus] = None
    category: Optional[TicketCategory] = None
    priority: Optional[TicketPriority] = None
    assigned_to: Optional[str] = None
    user_id: Optional[int] = None
    student_id: Optional[str] = None

class PaginatedTicketsResponse(BaseModel):
    tickets: List[TicketListResponse]
    total: int
    page: int
    per_page: int
    total_pages: int

# User info for ticket creation
class CurrentUser(BaseModel):
    id: int
    username: str
    email: str
    role: str 