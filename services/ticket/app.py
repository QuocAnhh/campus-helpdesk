from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import math
import logging

import database
import models
import schemas
import crud
import auth
from technical_integration import technical_agent

# Create tables in the database
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(
    title="Campus Helpdesk - Ticket Service",
    description="Service for managing support tickets",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "ticket"}

# Simple test endpoint
@app.post("/test-create")
async def test_create_ticket(
    ticket_data: dict,
    current_user: schemas.CurrentUser = Depends(auth.get_current_user)
):
    """Test endpoint for debugging ticket creation"""
    logger = logging.getLogger("ticket.test")
    logger.info("Test create ticket: user_id=%s data=%s", current_user.id, ticket_data)
    return {
        "status": "received",
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email
        },
        "data": ticket_data
    }

# Debug endpoint to check database content
@app.get("/debug/my-tickets")
async def debug_my_tickets(
    current_user: schemas.CurrentUser = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    """Debug endpoint to check actual database content"""
    logger = logging.getLogger("ticket.debug")
    tickets = crud.get_user_tickets(db=db, user_id=current_user.id, limit=5)
    debug_data = []
    for ticket in tickets:
        debug_data.append({
            "id": ticket.id,
            "subject": ticket.subject,
            "content": ticket.content,
            "content_length": len(ticket.content) if ticket.content else 0,
            "category": ticket.category.value if ticket.category else None,
            "priority": ticket.priority.value if ticket.priority else None,
            "status": ticket.status.value if ticket.status else None
        })
        logger.info("Ticket %d: subject=%s content_len=%d", 
                   ticket.id, ticket.subject[:30], len(ticket.content) if ticket.content else 0)
    return {
        "user_id": current_user.id,
        "tickets_found": len(tickets),
        "tickets": debug_data
    }

# ===== TICKET ENDPOINTS =====

@app.post("/tickets", response_model=schemas.TicketResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    ticket: schemas.TicketCreate,
    db: Session = Depends(database.get_db),
    current_user: schemas.CurrentUser = Depends(auth.get_current_user)
):
    """Create a new support ticket"""
    logger = logging.getLogger("ticket.create")
    logger.info("Creating ticket for user_id=%s subject=%s category=%s priority=%s", 
                current_user.id, ticket.subject[:50], ticket.category, ticket.priority)
    try:
        # Simple ticket creation without auto-detection to avoid issues
        # Auto-detection can be added later when technical_agent is properly tested
        logger.info("Input ticket data: subject_len=%d content_len=%d category=%s priority=%s",
                   len(ticket.subject), len(ticket.content), ticket.category, ticket.priority)
        
        db_ticket = crud.create_ticket(db=db, ticket=ticket, current_user=current_user)
        logger.info("Ticket created successfully id=%s", db_ticket.id)
        return db_ticket
    except Exception as e:
        logger.error("Error creating ticket for user_id=%s: %s", current_user.id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating ticket: {str(e)}"
        )

@app.get("/tickets", response_model=schemas.PaginatedTicketsResponse)
async def get_tickets(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[models.TicketStatus] = Query(None, description="Filter by status"),
    category: Optional[models.TicketCategory] = Query(None, description="Filter by category"),
    priority: Optional[models.TicketPriority] = Query(None, description="Filter by priority"),
    assigned_to: Optional[str] = Query(None, description="Filter by assigned user"),
    user_id: Optional[int] = Query(None, description="Filter by user ID (admin only)"),
    student_id: Optional[str] = Query(None, description="Filter by student ID"),
    db: Session = Depends(database.get_db),
    current_user: schemas.CurrentUser = Depends(auth.get_current_user)
):
    """Get tickets with filtering and pagination"""
    
    # Create filter object
    filters = schemas.TicketFilter(
        status=status,
        category=category,
        priority=priority,
        assigned_to=assigned_to,
        user_id=user_id if current_user.role == "admin" else None,
        student_id=student_id
    )
    
    # Calculate offset
    skip = (page - 1) * per_page
    
    # Get tickets and total count
    tickets = crud.get_tickets(
        db=db, 
        skip=skip, 
        limit=per_page, 
        filters=filters,
        current_user=current_user
    )
    
    total = crud.count_tickets(db=db, filters=filters, current_user=current_user)
    total_pages = math.ceil(total / per_page)
    
    return schemas.PaginatedTicketsResponse(
        tickets=tickets,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )

@app.get("/tickets/{ticket_id}", response_model=schemas.TicketResponse)
async def get_ticket(
    ticket_id: int,
    db: Session = Depends(database.get_db),
    current_user: schemas.CurrentUser = Depends(auth.get_current_user)
):
    """Get a specific ticket by ID"""
    db_ticket = crud.get_ticket(db=db, ticket_id=ticket_id)
    
    if not db_ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    # Check permissions: users can only see their own tickets, admins can see all
    if current_user.role != "admin" and db_ticket.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this ticket"
        )
    
    return db_ticket

@app.put("/tickets/{ticket_id}", response_model=schemas.TicketResponse)
async def update_ticket(
    ticket_id: int,
    ticket_update: schemas.TicketUpdate,
    db: Session = Depends(database.get_db),
    current_user: schemas.CurrentUser = Depends(auth.get_current_user)
):
    """Update a ticket"""
    db_ticket = crud.update_ticket(
        db=db, 
        ticket_id=ticket_id, 
        ticket_update=ticket_update,
        current_user=current_user
    )
    
    if not db_ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found or not authorized"
        )
    
    return db_ticket

@app.patch("/tickets/{ticket_id}/status", response_model=schemas.TicketResponse)
async def update_ticket_status(
    ticket_id: int,
    status_update: schemas.TicketStatusUpdate,
    db: Session = Depends(database.get_db),
    current_user: schemas.CurrentUser = Depends(auth.get_current_user)
):
    """Update ticket status"""
    db_ticket = crud.update_ticket_status(
        db=db,
        ticket_id=ticket_id,
        status_update=status_update,
        current_user=current_user
    )
    
    if not db_ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found or not authorized"
        )
    
    return db_ticket

@app.patch("/tickets/{ticket_id}/assign", response_model=schemas.TicketResponse)
async def assign_ticket(
    ticket_id: int,
    assigned_to: str,
    db: Session = Depends(database.get_db),
    current_user: schemas.CurrentUser = Depends(auth.get_current_admin_user)
):
    """Assign ticket to admin/agent (admin only)"""
    db_ticket = crud.assign_ticket(
        db=db,
        ticket_id=ticket_id,
        assigned_to=assigned_to,
        current_user=current_user
    )
    
    if not db_ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    return db_ticket

@app.delete("/tickets/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ticket(
    ticket_id: int,
    db: Session = Depends(database.get_db),
    current_user: schemas.CurrentUser = Depends(auth.get_current_admin_user)
):
    """Delete a ticket (admin only)"""
    success = crud.delete_ticket(db=db, ticket_id=ticket_id, current_user=current_user)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )

# ===== USER-SPECIFIC ENDPOINTS =====

@app.get("/my-tickets", response_model=List[schemas.TicketListResponse])
async def get_my_tickets(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(database.get_db),
    current_user: schemas.CurrentUser = Depends(auth.get_current_user)
):
    """Get current user's tickets"""
    tickets = crud.get_user_tickets(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )
    return tickets

# ===== ADMIN ENDPOINTS =====

@app.get("/admin/tickets/stats")
async def get_ticket_stats(
    db: Session = Depends(database.get_db),
    current_user: schemas.CurrentUser = Depends(auth.get_current_admin_user)
):
    """Get ticket statistics (admin only)"""
    stats = {
        "total": crud.count_tickets(db=db),
        "open": crud.count_tickets(db=db, filters=schemas.TicketFilter(status=models.TicketStatus.open)),
        "in_progress": crud.count_tickets(db=db, filters=schemas.TicketFilter(status=models.TicketStatus.in_progress)),
        "resolved": crud.count_tickets(db=db, filters=schemas.TicketFilter(status=models.TicketStatus.resolved)),
        "closed": crud.count_tickets(db=db, filters=schemas.TicketFilter(status=models.TicketStatus.closed))
    }
    return stats

@app.get("/admin/tickets/unassigned", response_model=List[schemas.TicketListResponse])
async def get_unassigned_tickets(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(database.get_db),
    current_user: schemas.CurrentUser = Depends(auth.get_current_admin_user)
):
    """Get unassigned tickets (admin only)"""
    filters = schemas.TicketFilter(assigned_to=None)
    tickets = crud.get_tickets(
        db=db,
        skip=skip,
        limit=limit,
        filters=filters,
        current_user=current_user
    )
    return tickets

# ===== INTEGRATION ENDPOINTS =====

@app.post("/tickets/{ticket_id}/technical-analysis")
async def request_technical_analysis(
    ticket_id: int,
    token: str = Depends(auth.oauth2_scheme),
    db: Session = Depends(database.get_db),
    current_user: schemas.CurrentUser = Depends(auth.get_current_user)
):
    """Request technical analysis from the technical agent"""
    # Get the ticket
    db_ticket = crud.get_ticket(db=db, ticket_id=ticket_id)
    
    if not db_ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    # Check permissions
    if current_user.role != "admin" and db_ticket.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    # Request analysis from technical agent
    analysis_result = await technical_agent.analyze_ticket(db_ticket, token)
    
    if analysis_result and analysis_result.get("success"):
        # Update ticket with analysis (could be stored in a separate table)
        return {
            "ticket_id": ticket_id,
            "analysis": analysis_result.get("analysis"),
            "agent_info": analysis_result.get("agent_info"),
            "sources": analysis_result.get("sources", []),
            "status": "completed"
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Technical analysis failed: {analysis_result.get('error', 'Unknown error')}"
        )

@app.post("/tickets/{ticket_id}/solution")
async def request_solution(
    ticket_id: int,
    token: str = Depends(auth.oauth2_scheme),
    db: Session = Depends(database.get_db),
    current_user: schemas.CurrentUser = Depends(auth.get_current_user)
):
    """Request solution suggestions from the technical agent"""
    # Get the ticket
    db_ticket = crud.get_ticket(db=db, ticket_id=ticket_id)
    
    if not db_ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    # Check permissions
    if current_user.role != "admin" and db_ticket.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    # Request solution from technical agent
    solution_result = await technical_agent.suggest_solution(db_ticket, token)
    
    if solution_result and solution_result.get("success"):
        return {
            "ticket_id": ticket_id,
            "solution": solution_result.get("solution"),
            "agent_info": solution_result.get("agent_info"),
            "status": "completed"
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Solution request failed: {solution_result.get('error', 'Unknown error')}"
        )

@app.patch("/tickets/{ticket_id}", response_model=schemas.TicketResponse)
async def patch_ticket(
    ticket_id: int,
    ticket_update: schemas.TicketUpdate,
    db: Session = Depends(database.get_db),
    current_user: schemas.CurrentUser = Depends(auth.get_current_user)
):
    """Partially update a ticket (PATCH method)"""
    db_ticket = crud.update_ticket(
        db=db, 
        ticket_id=ticket_id, 
        ticket_update=ticket_update,
        current_user=current_user
    )
    
    if not db_ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found or not authorized"
        )
    
    return db_ticket