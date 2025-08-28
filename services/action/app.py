from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, Optional
from sqlalchemy.orm import Session
import sys
import logging
import json
import time
from datetime import datetime
from jsonschema import validate, ValidationError
sys.path.append('/app')

from toolspec import TOOL_SCHEMAS
from models import ActionRequest, get_db, create_tables

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("action_service")

app = FastAPI(
    title="Action Service",
    description="Service for executing student self-service actions",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    """Create database tables on startup"""
    try:
        create_tables()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://localhost:5173",  # Vite dev server  
        "http://localhost:1610",  # Docker frontend port
        "http://localhost:80",    # Production frontend
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:1610",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ToolCallBody(BaseModel):
    tool_name: str
    tool_args: Dict[str, Any]

def validate_tool_args(tool_name: str, tool_args: Dict[str, Any]) -> None:
    """
    Validate tool arguments against JSON schema
    Raises HTTPException with detailed error messages
    """
    if tool_name not in TOOL_SCHEMAS:
        raise HTTPException(
            status_code=404, 
            detail=f"Tool '{tool_name}' not found. Available tools: {list(TOOL_SCHEMAS.keys())}"
        )
    
    schema = TOOL_SCHEMAS[tool_name]
    
    try:
        validate(instance=tool_args, schema=schema)
    except ValidationError as e:
        # Create detailed error message
        error_path = " -> ".join(str(p) for p in e.absolute_path) if e.absolute_path else "root"
        error_detail = {
            "error": "Validation failed",
            "field": error_path,
            "message": e.message,
            "invalid_value": e.instance if hasattr(e, 'instance') else None,
            "schema_requirement": schema
        }
        
        logger.warning(
            "Tool validation failed",
            extra={
                "tool_name": tool_name,
                "validation_error": error_detail,
                "provided_args": tool_args
            }
        )
        
        raise HTTPException(
            status_code=400,
            detail=error_detail
        )

def log_tool_call(tool_name: str, tool_args: Dict[str, Any], result: Dict[str, Any], duration_ms: float, request_id: int = None) -> None:
    """Log structured information about tool calls"""
    student_id = tool_args.get('student_id', 'unknown')
    
    log_data = {
        "event": "tool_call_completed",
        "tool_name": tool_name,
        "student_id": student_id,
        "request_id": request_id,
        "duration_ms": round(duration_ms, 2),
        "success": result.get("status") == "success",
        "args_count": len(tool_args),
        "result_summary": {
            "status": result.get("status"),
            "message": result.get("message", "")[:100]  # Truncate long messages
        }
    }
    
    logger.info(
        f"Tool call: {tool_name} for student {student_id} - {result.get('status')}",
        extra=log_data
    )

@app.post("/call_tool")
async def call_tool(b: ToolCallBody, request: Request, db: Session = Depends(get_db)):
    """
    Execute a tool with strict validation, database persistence, and structured logging
    """
    start_time = time.time()
    
    # Extract client info for logging
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    student_id = b.tool_args.get('student_id', 'unknown')
    
    logger.info(
        f"Tool call request: {b.tool_name}",
        extra={
            "event": "tool_call_started", 
            "tool_name": b.tool_name,
            "student_id": student_id,
            "client_ip": client_ip,
            "user_agent": user_agent,
            "args_provided": list(b.tool_args.keys())
        }
    )
    
    # Strict validation against JSON schema
    validate_tool_args(b.tool_name, b.tool_args)
    
    # Create database record
    action_request = ActionRequest(
        student_id=student_id,
        action_type=b.tool_name,
        status="submitted",
        request_data=b.tool_args,
        client_ip=client_ip,
        user_agent=user_agent
    )
    db.add(action_request)
    db.commit()
    db.refresh(action_request)
    
    try:
        # Route to appropriate stub function
        if b.tool_name == "reset_password":
            result = reset_password_stub(b.tool_args)
        elif b.tool_name == "renew_library_card":
            result = renew_library_card_stub(b.tool_args)
        elif b.tool_name == "create_glpi_ticket":
            result = create_glpi_ticket_stub(b.tool_args)
        elif b.tool_name == "request_dorm_fix":
            result = request_dorm_fix_stub(b.tool_args)
        elif b.tool_name == "book_room":
            result = book_room_stub(b.tool_args)
        else:
            raise HTTPException(status_code=404, detail=f"Tool '{b.tool_name}' implementation not found")
        
        # Update database with result
        action_request.status = "completed"
        action_request.result_data = result
        action_request.external_id = result.get("ticket_id") or result.get("booking_id") or result.get("request_id")
        action_request.processed_at = datetime.utcnow()
        db.commit()
        
        # Calculate duration and log
        duration_ms = (time.time() - start_time) * 1000
        log_tool_call(b.tool_name, b.tool_args, result, duration_ms, action_request.id)
        
        return result
        
    except HTTPException:
        # Update database with failure
        action_request.status = "failed"
        action_request.result_data = {"status": "failed", "error": "HTTP Exception"}
        action_request.processed_at = datetime.utcnow()
        db.commit()
        raise
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        
        # Update database with failure
        action_request.status = "failed"
        action_request.result_data = {"status": "failed", "error": str(e)}
        action_request.processed_at = datetime.utcnow()
        db.commit()
        
        logger.error(
            f"Tool call failed: {b.tool_name}",
            extra={
                "event": "tool_call_error",
                "tool_name": b.tool_name,
                "student_id": b.tool_args.get('student_id', 'unknown'),
                "request_id": action_request.id,
                "duration_ms": round(duration_ms, 2),
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=500, 
            detail=f"Internal error executing tool '{b.tool_name}': {str(e)}"
        )

# Admin API endpoints for action requests management
from sqlalchemy import desc

class ActionRequestOut(BaseModel):
    id: int
    student_id: str
    action_type: str
    status: str
    request_data: Dict[str, Any]
    result_data: Optional[Dict[str, Any]] = None
    external_id: Optional[str] = None
    submitted_at: str  # Will be serialized as ISO string
    processed_at: Optional[str] = None
    processed_by: Optional[str] = None
    notes: Optional[str] = None
    client_ip: Optional[str] = None

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

@app.get("/admin/action-requests")
async def get_action_requests(
    db: Session = Depends(get_db),
    status: Optional[str] = None,
    action_type: Optional[str] = None,
    student_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
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
    
    # Convert to dict for JSON serialization
    result = []
    for req in requests:
        result.append({
            "id": req.id,
            "student_id": req.student_id,
            "action_type": req.action_type,
            "status": req.status,
            "request_data": req.request_data,
            "result_data": req.result_data,
            "external_id": req.external_id,
            "submitted_at": req.submitted_at.isoformat() if req.submitted_at else None,
            "processed_at": req.processed_at.isoformat() if req.processed_at else None,
            "processed_by": req.processed_by,
            "notes": req.notes,
            "client_ip": req.client_ip
        })
    
    return result

@app.get("/admin/action-requests/stats")
async def get_action_request_stats(db: Session = Depends(get_db)):
    """Get statistics about action requests"""
    total = db.query(ActionRequest).count()
    submitted = db.query(ActionRequest).filter(ActionRequest.status == "submitted").count()
    in_progress = db.query(ActionRequest).filter(ActionRequest.status == "in_progress").count()
    completed = db.query(ActionRequest).filter(ActionRequest.status == "completed").count()
    failed = db.query(ActionRequest).filter(ActionRequest.status == "failed").count()
    cancelled = db.query(ActionRequest).filter(ActionRequest.status == "cancelled").count()
    
    return {
        "total": total,
        "submitted": submitted,
        "in_progress": in_progress,
        "completed": completed,
        "failed": failed,
        "cancelled": cancelled
    }

@app.get("/admin/action-requests/{request_id}")
async def get_action_request(request_id: int, db: Session = Depends(get_db)):
    """Get specific action request by ID"""
    request = db.query(ActionRequest).filter(ActionRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Action request not found")
    
    return {
        "id": request.id,
        "student_id": request.student_id,
        "action_type": request.action_type,
        "status": request.status,
        "request_data": request.request_data,
        "result_data": request.result_data,
        "external_id": request.external_id,
        "submitted_at": request.submitted_at.isoformat() if request.submitted_at else None,
        "processed_at": request.processed_at.isoformat() if request.processed_at else None,
        "processed_by": request.processed_by,
        "notes": request.notes,
        "client_ip": request.client_ip
    }

@app.patch("/admin/action-requests/{request_id}")
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
    
    return {"message": "Action request updated successfully"}

# Stub functions
def reset_password_stub(args: Dict):
    logger.info("Called reset_password with args=%s", args)
    return {"status": "success", "message": "Password reset link sent."}

def renew_library_card_stub(args: Dict):
    logger.info("Called renew_library_card with args=%s", args)
    duration = args.get("duration", "6_months")
    return {"status": "success", "message": f"Library card renewed for {duration}.", "new_expiry": "2026-02-28"}

def create_glpi_ticket_stub(args: Dict):
    logger.info("Called create_glpi_ticket with args=%s", args)
    return {"status": "success", "ticket_id": "12345"}

def request_dorm_fix_stub(args: Dict):
    logger.info("Called request_dorm_fix with args=%s", args)
    return {"status": "success", "request_id": "abcde"}

def book_room_stub(args: Dict):
    logger.info("Called book_room with args=%s", args)
    return {"status": "success", "booking_id": "xyz-789"}