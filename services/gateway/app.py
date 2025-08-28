from fastapi import FastAPI, HTTPException, Response, Request, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import os
import uuid
import json
from redis import Redis
import httpx
import sys
import logging
import time
from jose import JWTError, jwt
sys.path.append('/app')
from agents import AgentManager
from routers import auth as auth_router
from routers import users as user_router
from routers import tickets as ticket_router

# --- Setup ---
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
TICKET_URL = os.getenv("TICKET_URL", "http://ticket:8000")
ACTION_URL = os.getenv("ACTION_URL", "http://action:8000")
DEFAULT_SECRET = "a_very_secret_key_that_should_be_changed"
SECRET_KEY_ENV = os.getenv("SECRET_KEY", DEFAULT_SECRET)

logger = logging.getLogger("gateway")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(message)s')
# Elevate tickets proxy logging for debugging auth until resolved
logging.getLogger("routers.tickets").setLevel(logging.DEBUG)
logging.getLogger("gateway.security").setLevel(logging.DEBUG)

r = Redis.from_url(REDIS_URL, decode_responses=True)

app = FastAPI(title="Campus Helpdesk Gateway")

# --- Lifespan: shared HTTP client ---
@app.on_event("startup")
async def _startup():
    if SECRET_KEY_ENV == DEFAULT_SECRET:
        logger.warning("Using default SECRET_KEY. Set a strong SECRET_KEY in environment for production.")
    app.state.http_client = httpx.AsyncClient(timeout=10.0)

@app.on_event("shutdown")
async def _shutdown():
    client: httpx.AsyncClient = getattr(app.state, "http_client", None)  # type: ignore
    if client:
        await client.aclose()

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=False,  # Must be False when allow_origins is "*"
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers ---
app.include_router(auth_router.router)
app.include_router(user_router.router)
app.include_router(ticket_router.router)

# Backward compatibility: legacy /my-tickets endpoint now proxies directly to avoid redirect header issues
@app.get("/my-tickets")
async def legacy_my_tickets(request: Request):
    """Legacy route kept for older frontend versions. Direct proxy to ticket service /my-tickets (no redirect)."""
    target_url = f"{ticket_router.TICKET_URL}/my-tickets"
    if request.url.query:
        target_url += f"?{request.url.query}"
    logger.debug("Legacy /my-tickets direct proxy -> %s", target_url)
    return await ticket_router._proxy_request(request, target_url)  # type: ignore

# --- Initialize Agent Manager ---
agent_manager = AgentManager()

# --- Chat History Management ---
def get_chat_history(session_id: str, limit: int = 10) -> List[Dict]:
    if not session_id:
        return []
    key = f"chat_history:{session_id}"
    history = r.lrange(key, 0, limit - 1)
    return [json.loads(h) for h in reversed(history)]

def add_to_chat_history(session_id: str, user_message: str, bot_message: str, agent_info: Dict = None, student_id: str = None):
    if not session_id:
        return
    key = f"chat_history:{session_id}"
    turn = {
        "user": user_message,
        "bot": bot_message,
        "timestamp": time.time(),
        "agent": agent_info.get("agent", "unknown") if agent_info else "unknown",
        "student_id": student_id
    }
    r.lpush(key, json.dumps(turn))
    r.ltrim(key, 0, 99)
    # Set/refresh TTL for chat history key to align with session metadata
    r.expire(key, 86400)
    
    # Kiểm tra từ khóa kết thúc cuộc hội thoại
    ending_keywords = ["tạm biệt", "bye", "cảm ơn", "thanks", "xong rồi", "hết rồi", "ok cảm ơn", "được rồi", "đã hiểu"]
    is_ending = any(keyword in user_message.lower() for keyword in ending_keywords)
    
    # Lưu session metadata
    session_key = f"session_meta:{session_id}"
    existing_status = r.hget(session_key, "status")
    
    # Nếu đã completed thì không thay đổi status
    new_status = "completed" if is_ending else (existing_status or "active")
    
    session_data = {
        "session_id": session_id,
        "student_id": student_id or "N/A",
        "last_activity": time.time(),
        "status": new_status
    }
    r.hset(session_key, mapping=session_data)
    r.expire(session_key, 86400)  # Expire after 24 hours

# --- Student ID Extraction ---
def extract_student_id_from_jwt(token: str) -> Optional[str]:
    """Extract student_id from JWT token"""
    try:
        from security import SECRET_KEY, ALGORITHM
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # Assuming student_id is stored in the JWT payload
        # For now, we'll use the username as student_id
        return payload.get("sub")  # subject is typically the username/student_id
    except JWTError:
        return None

def get_student_id(
    authorization: Optional[str] = Header(None),
    x_student_id: Optional[str] = Header(None, alias="x-student-id")
) -> Optional[str]:
    """Extract student_id from Authorization header (JWT) or x-student-id header (dev fallback)"""
    # Try JWT first
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        student_id = extract_student_id_from_jwt(token)
        if student_id:
            return student_id
    
    # Fallback to x-student-id header for development
    return x_student_id

# --- New Pydantic Models ---
class UserProfile(BaseModel):
    student_id: str
    name: str = "Unknown"
    major: str = "Unknown"

class TicketSummary(BaseModel):
    id: int
    subject: str
    category: str
    priority: str
    status: str
    created_at: str

class ChatMessage(BaseModel):
    user: str
    bot: str
    timestamp: float
    agent: str
    student_id: Optional[str] = None

# --- Pydantic Models ---
class AskBody(BaseModel):
    channel: str
    text: str
    student_id: str | None = None
    session_id: str | None = None

# --- Main Endpoint ---
@app.post("/ask")
async def ask(body: AskBody):
    """
    Endpoint chính để xử lý yêu cầu từ sinh viên thông qua hệ thống multi-agent
    """
    req_id = str(uuid.uuid4())
    chat_history = get_chat_history(body.session_id)
    
    try:
        # Xử lý tin nhắn thông qua Agent Manager
        response = await agent_manager.process_message(
            user_message=body.text,
            chat_history=chat_history,
            session_id=body.session_id
        )
        
        final_reply = response.get("reply", "Xin lỗi, tôi không thể xử lý yêu cầu này.")
        
        # Cập nhật lịch sử chat
        add_to_chat_history(body.session_id, body.text, final_reply, response, body.student_id)
        
        # Trả về response
        return {
            "request_id": req_id,
            "answer": {
                "reply": final_reply,
                "agent_info": {
                    "agent": response.get("agent", "unknown"),
                    "routing_info": response.get("routing_info", {}),
                    "suggested_action": response.get("suggested_action"),
                    "sources": response.get("sources", [])
                }
            }
        }
        
    except Exception as e:
        logger.exception("Error in /ask endpoint: %s", e)
        return {
            "request_id": req_id,
            "answer": {
                "reply": "Xin lỗi, hệ thống đang gặp sự cố. Bạn vui lòng thử lại sau.",
                "agent_info": {
                    "agent": "error",
                    "routing_info": {"error": str(e)}
                }
            }
        }

# --- Health Check ---
@app.get("/health")
async def health_check():
    """Kiểm tra tình trạng hệ thống"""
    available_agents = agent_manager.get_available_agents()
    return {
        "status": "healthy",
        "available_agents": available_agents,
        "total_agents": len(available_agents)
    }

# --- Agent Info ---
@app.get("/agents")
async def get_agents():
    """Lấy thông tin về các agent có sẵn"""
    return {
        "available_agents": agent_manager.get_available_agents(),
        "description": "Multi-agent system for Campus Helpdesk"
    }

# --- Chat Logs ---
@app.get("/chat-logs")
async def get_chat_logs():
    """Lấy danh sách các chat logs từ Redis"""
    try:
        logs = []
        # Use scan_iter to avoid blocking Redis
        for key in r.scan_iter(match="chat_history:*", count=100):
            session_id = key.replace("chat_history:", "")
            history_raw = r.lrange(key, 0, -1)  # newest -> oldest
            if not history_raw:
                continue
            # Convert and reverse once for chronological order oldest -> newest
            messages = [json.loads(h) for h in reversed(history_raw)]
            first_msg = messages[0]
            last_msg = messages[-1]
            session_key = f"session_meta:{session_id}"
            session_meta = r.hgetall(session_key)
            current_time = time.time()
            last_activity = float(session_meta.get("last_activity", current_time))
            stored_status = session_meta.get("status", "active")
            if stored_status == "completed":
                is_active = False
            else:
                is_active = (current_time - last_activity) < 1800
            start_time = first_msg.get("timestamp", current_time - len(messages) * 60)
            end_time = last_msg.get("timestamp", current_time)
            student_id = session_meta.get("student_id") or first_msg.get("student_id", "N/A")
            agents_used = [msg.get("agent", "unknown") for msg in messages if msg.get("agent")]
            main_agent = max(set(agents_used), key=agents_used.count) if agents_used else "unknown"
            logs.append({
                "id": session_id,
                "session_id": session_id,
                "student_id": student_id,
                "messages_count": len(messages),
                "start_time": start_time,
                "end_time": end_time,
                "status": "active" if is_active else "completed",
                "last_message": last_msg.get("user", "")[:50] + ("..." if len(last_msg.get("user", "")) > 50 else ""),
                "agent": main_agent
            })
        logs.sort(key=lambda x: x["end_time"], reverse=True)
        return {"logs": logs, "total": len(logs)}
    except Exception as e:
        logger.exception("Error getting chat logs: %s", e)
        return {"logs": [], "total": 0}

@app.get("/chat-logs/{session_id}")
async def get_chat_log_detail(session_id: str):
    """Lấy chi tiết một phiên chat"""
    try:
        history = get_chat_history(session_id, limit=100)
        return {"session_id": session_id, "messages": history, "total_messages": len(history)}
    except Exception as e:
        logger.exception("Error getting chat log detail: %s", e)
        return {"session_id": session_id, "messages": [], "total_messages": 0}

@app.post("/chat-logs/{session_id}/complete")
async def mark_session_complete(session_id: str):
    """Đánh dấu session hoàn thành"""
    try:
        session_key = f"session_meta:{session_id}"
        if r.exists(session_key):
            r.hset(session_key, "status", "completed")
            return {"message": "Session marked as completed", "session_id": session_id}
        else:
            raise HTTPException(status_code=404, detail="Session not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error marking session complete: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/chat-logs/{session_id}/reopen")
async def reopen_session(session_id: str):
    """Mở lại session"""
    try:
        session_key = f"session_meta:{session_id}"
        if r.exists(session_key):
            r.hset(session_key, "status", "active")
            r.hset(session_key, "last_activity", time.time())
            return {"message": "Session reopened", "session_id": session_id}
        else:
            raise HTTPException(status_code=404, detail="Session not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error reopening session: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")

# --- New Endpoints ---

@app.get("/me", response_model=UserProfile)
async def get_me(student_id: Optional[str] = Depends(get_student_id)):
    """Get current user profile information"""
    if not student_id:
        raise HTTPException(
            status_code=401, 
            detail="Student ID not found in JWT or x-student-id header"
        )
    
    # For development, return mock data
    # Later this should connect to SIS (Student Information System)
    return UserProfile(
        student_id=student_id,
        name="Unknown",
        major="Unknown"
    )

@app.get("/me/tickets", response_model=List[TicketSummary])
async def get_my_tickets(
    request: Request,
    student_id: Optional[str] = Depends(get_student_id)
):
    """Get current user's tickets"""
    if not student_id:
        raise HTTPException(
            status_code=401,
            detail="Student ID not found in JWT or x-student-id header"
        )
    
    try:
        # Proxy to ticket service with student_id filter
        target_url = f"{TICKET_URL}/tickets?student_id={student_id}"
        if request.url.query:
            target_url += f"&{request.url.query}"
        
        # Use the shared HTTP client
        client: httpx.AsyncClient = app.state.http_client
        
        # Forward authorization header if present
        headers = {}
        if request.headers.get("authorization"):
            headers["authorization"] = request.headers.get("authorization")
        
        response = await client.get(target_url, headers=headers)
        
        if response.status_code == 404:
            return []  # Return empty list if no tickets found
        elif response.status_code != 200:
            logger.error("Ticket service error: %s - %s", response.status_code, response.text)
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Ticket service error: {response.text}"
            )
        
        tickets_data = response.json()
        
        # Transform to TicketSummary format
        tickets = []
        if isinstance(tickets_data, dict) and "tickets" in tickets_data:
            tickets_list = tickets_data["tickets"]
        elif isinstance(tickets_data, list):
            tickets_list = tickets_data
        else:
            tickets_list = []
        
        for ticket in tickets_list:
            tickets.append(TicketSummary(
                id=ticket.get("id"),
                subject=ticket.get("subject", ""),
                category=ticket.get("category", ""),
                priority=ticket.get("priority", ""),
                status=ticket.get("status", ""),
                created_at=ticket.get("created_at", "")
            ))
        
        return tickets
        
    except httpx.RequestError as e:
        logger.error("Error connecting to ticket service: %s", e)
        raise HTTPException(
            status_code=503,
            detail="Ticket service unavailable"
        )
    except Exception as e:
        logger.error("Error in get_my_tickets: %s", e)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@app.get("/sessions/{session_id}/history", response_model=List[ChatMessage])
async def get_session_history(
    session_id: str,
    student_id: Optional[str] = Depends(get_student_id),
    limit: int = 50
):
    """Get chat history for a specific session"""
    if not student_id:
        raise HTTPException(
            status_code=401,
            detail="Student ID not found in JWT or x-student-id header"
        )
    
    try:
        # Get chat history from Redis
        history = get_chat_history(session_id, limit)
        
        # Filter by student_id for security (users should only see their own sessions)
        filtered_history = []
        for message in history:
            msg_student_id = message.get("student_id")
            # Allow if no student_id in message (legacy) or if it matches
            if not msg_student_id or msg_student_id == student_id:
                filtered_history.append(ChatMessage(
                    user=message.get("user", ""),
                    bot=message.get("bot", ""),
                    timestamp=message.get("timestamp", 0),
                    agent=message.get("agent", "unknown"),
                    student_id=message.get("student_id")
                ))
        
        return filtered_history
        
    except Exception as e:
        logger.error("Error getting session history: %s", e)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

# --- Action Service Integration ---
ACTION_URL = os.getenv("ACTION_URL", "http://action:8000")

class ToolCallRequest(BaseModel):
    tool_name: str
    tool_args: Dict

class ToolCallResponse(BaseModel):
    status: str
    message: Optional[str] = None
    booking_id: Optional[str] = None
    ticket_id: Optional[str] = None
    request_id: Optional[str] = None

@app.post("/call_tool", response_model=ToolCallResponse)
async def call_tool(
    request: ToolCallRequest,
    student_id: Optional[str] = Depends(get_student_id)
):
    """Proxy tool calls to action service with authentication"""
    if not student_id:
        raise HTTPException(
            status_code=401,
            detail="Student ID not found in JWT or x-student-id header"
        )
    
    try:
        # Add student_id to tool_args if not present
        if "student_id" not in request.tool_args:
            request.tool_args["student_id"] = student_id
        
        # Forward request to action service
        client: httpx.AsyncClient = app.state.http_client
        response = await client.post(
            f"{ACTION_URL}/call_tool",
            json={
                "tool_name": request.tool_name,
                "tool_args": request.tool_args
            },
            timeout=30.0
        )
        
        if response.status_code == 400:
            # Forward validation errors from action service
            error_detail = response.json()
            raise HTTPException(status_code=400, detail=error_detail)
        elif response.status_code == 404:
            error_detail = response.json()
            raise HTTPException(status_code=404, detail=error_detail)
        elif response.status_code != 200:
            logger.error("Action service error: %s - %s", response.status_code, response.text)
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Action service error: {response.text}"
            )
        
        result = response.json()
        return ToolCallResponse(**result)
        
    except httpx.RequestError as e:
        logger.error("Error connecting to action service: %s", e)
        raise HTTPException(
            status_code=503,
            detail="Action service unavailable"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error in call_tool: %s", e)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@app.get("/tools")
async def get_available_tools():
    """Get list of available tools from Action service"""
    try:
        client: httpx.AsyncClient = app.state.http_client
        response = await client.get(f"{ACTION_URL}/tools", timeout=10.0)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"tools": [], "error": "Could not fetch tools from action service"}
    
    except Exception as e:
        logger.error(f"Error fetching tools: {e}")
        return {"tools": [], "error": str(e)}

# --- Workflow Management Routes

@app.get("/workflows/{workflow_id}")
async def get_workflow_status(workflow_id: str):
    """Get status of a workflow"""
    try:
        workflow_status = agent_manager.get_workflow_status(workflow_id)
        if workflow_status:
            return workflow_status
        else:
            raise HTTPException(status_code=404, detail="Workflow not found")
    except Exception as e:
        logger.error(f"Error getting workflow status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/evaluate")
async def evaluate_response(
    response_data: Dict[str, Any],
    original_request: str,
    context: Optional[Dict[str, Any]] = None
):
    """Evaluate response quality using Critic Agent"""
    try:
        evaluation = await agent_manager.evaluate_response_quality(
            response=response_data,
            original_request=original_request,
            context=context or {}
        )
        return evaluation
    except Exception as e:
        logger.error(f"Error in response evaluation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# --- Admin Action Requests Management Routes

@app.get("/admin/action-requests")
async def admin_get_action_requests(
    request: Request,
    status: Optional[str] = None,
    action_type: Optional[str] = None,
    student_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """Proxy admin action requests list to action service"""
    try:
        client = app.state.http_client
        params = {}
        if status:
            params["status"] = status
        if action_type:
            params["action_type"] = action_type
        if student_id:
            params["student_id"] = student_id
        params["limit"] = limit
        params["offset"] = offset
        
        response = await client.get(
            f"{ACTION_URL}/admin/action-requests",
            params=params,
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()
        
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Action service unavailable")
    except Exception as e:
        logger.error("Error in admin_get_action_requests: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/admin/action-requests/{request_id}")
async def admin_get_action_request(request_id: int, request: Request):
    """Proxy admin action request details to action service"""
    try:
        client = app.state.http_client
        response = await client.get(
            f"{ACTION_URL}/admin/action-requests/{request_id}",
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()
        
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Action service unavailable")
    except Exception as e:
        logger.error("Error in admin_get_action_request: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/admin/action-requests-stats")
async def admin_get_action_requests_stats(request: Request):
    """Proxy admin action requests stats to action service"""
    try:
        client = app.state.http_client
        response = await client.get(
            f"{ACTION_URL}/admin/action-requests/stats",
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()
        
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Action service unavailable")
    except Exception as e:
        logger.error("Error in admin_get_action_requests_stats: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.patch("/admin/action-requests/{request_id}")
async def admin_update_action_request(request_id: int, request: Request):
    """Proxy admin action request update to action service"""
    try:
        client = app.state.http_client
        body = await request.body()
        
        response = await client.patch(
            f"{ACTION_URL}/admin/action-requests/{request_id}",
            content=body,
            headers={"Content-Type": "application/json"},
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()
        
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Action service unavailable")
    except Exception as e:
        logger.error("Error in admin_update_action_request: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")
