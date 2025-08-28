from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from typing import List, Optional
from datetime import datetime
import models
import schemas

def create_ticket(db: Session, ticket: schemas.TicketCreate, current_user: schemas.CurrentUser) -> models.Ticket:
    """Create a new ticket"""
    db_ticket = models.Ticket(
        subject=ticket.subject,
        content=ticket.content,
        category=ticket.category,
        priority=ticket.priority,
        user_id=current_user.id,
        user_name=current_user.username,
        user_email=current_user.email,
        student_id=ticket.student_id
    )
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket

def get_ticket(db: Session, ticket_id: int) -> Optional[models.Ticket]:
    """Get a single ticket by ID"""
    return db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()

def get_tickets(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    filters: Optional[schemas.TicketFilter] = None,
    current_user: Optional[schemas.CurrentUser] = None
) -> List[models.Ticket]:
    """Get tickets with filtering and pagination"""
    query = db.query(models.Ticket)
    
    # Apply filters
    if filters:
        if filters.status:
            query = query.filter(models.Ticket.status == filters.status)
        if filters.category:
            query = query.filter(models.Ticket.category == filters.category)
        if filters.priority:
            query = query.filter(models.Ticket.priority == filters.priority)
        if filters.assigned_to:
            query = query.filter(models.Ticket.assigned_to == filters.assigned_to)
        if filters.user_id:
            query = query.filter(models.Ticket.user_id == filters.user_id)
        if filters.student_id:
            query = query.filter(models.Ticket.student_id == filters.student_id)
    
    # If user is not admin, only show their own tickets
    if current_user and current_user.role != "admin":
        query = query.filter(models.Ticket.user_id == current_user.id)
    
    # Order by creation date (newest first)
    query = query.order_by(desc(models.Ticket.created_at))
    
    return query.offset(skip).limit(limit).all()

def count_tickets(
    db: Session,
    filters: Optional[schemas.TicketFilter] = None,
    current_user: Optional[schemas.CurrentUser] = None
) -> int:
    """Count tickets with filtering"""
    query = db.query(models.Ticket)
    
    # Apply same filters as get_tickets
    if filters:
        if filters.status:
            query = query.filter(models.Ticket.status == filters.status)
        if filters.category:
            query = query.filter(models.Ticket.category == filters.category)
        if filters.priority:
            query = query.filter(models.Ticket.priority == filters.priority)
        if filters.assigned_to:
            query = query.filter(models.Ticket.assigned_to == filters.assigned_to)
        if filters.user_id:
            query = query.filter(models.Ticket.user_id == filters.user_id)
        if filters.student_id:
            query = query.filter(models.Ticket.student_id == filters.student_id)
    
    # If user is not admin, only count their own tickets
    if current_user and current_user.role != "admin":
        query = query.filter(models.Ticket.user_id == current_user.id)
    
    return query.count()

def update_ticket(
    db: Session,
    ticket_id: int,
    ticket_update: schemas.TicketUpdate,
    current_user: schemas.CurrentUser
) -> Optional[models.Ticket]:
    """Update a ticket"""
    db_ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    
    if not db_ticket:
        return None
    
    # Check permissions: only ticket owner or admin can update
    if current_user.role != "admin" and db_ticket.user_id != current_user.id:
        return None
    
    # Update fields
    update_data = ticket_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        if hasattr(db_ticket, field):
            setattr(db_ticket, field, value)
    
    # Update resolved_at if status changed to resolved
    if ticket_update.status == models.TicketStatus.resolved and db_ticket.resolved_at is None:
        db_ticket.resolved_at = datetime.utcnow()
    
    db_ticket.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_ticket)
    return db_ticket

def update_ticket_status(
    db: Session,
    ticket_id: int,
    status_update: schemas.TicketStatusUpdate,
    current_user: schemas.CurrentUser
) -> Optional[models.Ticket]:
    """Update ticket status (admin only for certain statuses)"""
    db_ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    
    if not db_ticket:
        return None
    
    # Check permissions
    if current_user.role != "admin" and db_ticket.user_id != current_user.id:
        return None
    
    # Only admin can set status to in_progress or assign tickets
    if status_update.status == models.TicketStatus.in_progress and current_user.role != "admin":
        return None
    
    db_ticket.status = status_update.status
    
    if status_update.resolution:
        db_ticket.resolution = status_update.resolution
    
    # Set resolved_at when status changes to resolved
    if status_update.status == models.TicketStatus.resolved:
        db_ticket.resolved_at = datetime.utcnow()
    
    db_ticket.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_ticket)
    return db_ticket

def delete_ticket(db: Session, ticket_id: int, current_user: schemas.CurrentUser) -> bool:
    """Delete a ticket (admin only)"""
    if current_user.role != "admin":
        return False
    
    db_ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    
    if not db_ticket:
        return False
    
    db.delete(db_ticket)
    db.commit()
    return True

def assign_ticket(
    db: Session,
    ticket_id: int,
    assigned_to: str,
    current_user: schemas.CurrentUser
) -> Optional[models.Ticket]:
    """Assign ticket to admin/agent (admin only)"""
    if current_user.role != "admin":
        return None
    
    db_ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    
    if not db_ticket:
        return None
    
    db_ticket.assigned_to = assigned_to
    db_ticket.status = models.TicketStatus.in_progress
    db_ticket.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_ticket)
    return db_ticket

def get_user_tickets(db: Session, user_id: int, skip: int = 0, limit: int = 20) -> List[models.Ticket]:
    """Get all tickets for a specific user"""
    return db.query(models.Ticket)\
        .filter(models.Ticket.user_id == user_id)\
        .order_by(desc(models.Ticket.created_at))\
        .offset(skip)\
        .limit(limit)\
        .all()

def get_tickets_by_status(db: Session, status: models.TicketStatus, skip: int = 0, limit: int = 20) -> List[models.Ticket]:
    """Get tickets by status"""
    return db.query(models.Ticket)\
        .filter(models.Ticket.status == status)\
        .order_by(desc(models.Ticket.created_at))\
        .offset(skip)\
        .limit(limit)\
        .all() 