from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class Interaction(BaseModel):
    channel: str  # zalo/mail/...
    text: str
    student_id: Optional[str] = None
    meta: Dict[str, str] = Field(default_factory=dict)

class Intent(BaseModel):
    label: str
    confidencies: float = 1.0
    entities: Dict[str, str] = Field(default_factory=dict)

class PolicyCitation(BaseModel):
    doc: str
    section: str
    quote: str
    url: Optional[str] = None

class Answer(BaseModel):
    reply: str
    citations: List[PolicyCitation] = Field(default_factory=list)

class Ticket(BaseModel):
    id: str
    subject: str
    category: str
    priority: str = "normal"
    status: str = "open"
    created_at: datetime
    updated_at: datetime
    interactions: List[Interaction] = Field(default_factory=list)
    answer: Optional[Answer] = None
    meta: Dict[str, Any] = Field(default_factory=dict)

