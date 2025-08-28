# Admin CRUD operations for Action Requests

from fastapi import Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from models import ActionRequest, get_db

# Pydantic schemas for API
class ActionRequestOut(BaseModel):
    id: int
    student_id: str
    action_type: str
    status: str
    request_data: dict
    result_data: Optional[dict] = None
    external_id: Optional[str] = None
    submitted_at: datetime
    processed_at: Optional[datetime] = None
    processed_by: Optional[str] = None
    notes: Optional[str] = None
    client_ip: Optional[str] = None
    
    class Config:
        from_attributes = True

class ActionRequestUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    processed_by: Optional[str] = None

class ActionRequestStats(BaseModel):
    total: int
    submitted: int
    in_progress: int
    completed: int
    failed: int
    cancelled: int

# Admin API endpoints
@app.get("/admin/action-requests", response_model=List[ActionRequestOut])
async def get_action_requests(
    db: Session = Depends(get_db),
    status: Optional[str] = Query(None, description="Filter by status"),
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    student_id: Optional[str] = Query(None, description="Filter by student ID"),
    limit: int = Query(50, le=100, description="Limit number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
):
    """Get list of action requests with optional filtering"""
    query = db.query(ActionRequest)
    
    # Apply filters
    if status:
        query = query.filter(ActionRequest.status == status)
    if action_type:
        query = query.filter(ActionRequest.action_type == action_type)
    if student_id:
        query = query.filter(ActionRequest.student_id == student_id)
    
    # Order by most recent first
    query = query.order_by(desc(ActionRequest.submitted_at))
    
    # Apply pagination
    requests = query.offset(offset).limit(limit).all()
    
    return requests

@app.get("/admin/action-requests/{request_id}", response_model=ActionRequestOut)
async def get_action_request(request_id: int, db: Session = Depends(get_db)):
    """Get specific action request by ID"""
    request = db.query(ActionRequest).filter(ActionRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Action request not found")
    return request

@app.patch("/admin/action-requests/{request_id}", response_model=ActionRequestOut)
async def update_action_request(
    request_id: int, 
    update_data: ActionRequestUpdate,
    db: Session = Depends(get_db)
):
    """Update action request status and notes"""
    request = db.query(ActionRequest).filter(ActionRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Action request not found")
    
    # Update fields
    if update_data.status:
        request.status = update_data.status
        request.processed_at = datetime.utcnow()
    if update_data.notes:
        request.notes = update_data.notes
    if update_data.processed_by:
        request.processed_by = update_data.processed_by
    
    db.commit()
    db.refresh(request)
    
    logger.info(
        f"Action request {request_id} updated",
        extra={
            "event": "admin_update_request",
            "request_id": request_id,
            "student_id": request.student_id,
            "new_status": request.status,
            "updated_by": update_data.processed_by
        }
    )
    
    return request

@app.get("/admin/action-requests/stats", response_model=ActionRequestStats)
async def get_action_request_stats(db: Session = Depends(get_db)):
    """Get statistics about action requests"""
    total = db.query(ActionRequest).count()
    submitted = db.query(ActionRequest).filter(ActionRequest.status == "submitted").count()
    in_progress = db.query(ActionRequest).filter(ActionRequest.status == "in_progress").count()
    completed = db.query(ActionRequest).filter(ActionRequest.status == "completed").count()
    failed = db.query(ActionRequest).filter(ActionRequest.status == "failed").count()
    cancelled = db.query(ActionRequest).filter(ActionRequest.status == "cancelled").count()
    
    return ActionRequestStats(
        total=total,
        submitted=submitted,
        in_progress=in_progress,
        completed=completed,
        failed=failed,
        cancelled=cancelled
    )
