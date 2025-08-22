from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
import os
import uuid
import json
from redis import Redis
import sys
sys.path.append('/app')
from agents import AgentManager
from routers import auth as auth_router
from routers import users as user_router

# --- Setup ---
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
r = Redis.from_url(REDIS_URL, decode_responses=True)

app = FastAPI(title="Campus Helpdesk Gateway")

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
    
    import time
    turn = {
        "user": user_message, 
        "bot": bot_message,
        "timestamp": time.time(),
        "agent": agent_info.get("agent", "unknown") if agent_info else "unknown",
        "student_id": student_id
    }
    r.lpush(key, json.dumps(turn))
    r.ltrim(key, 0, 99)
    
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
        print(f"Error in /ask endpoint: {e}")
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
        # Lấy tất cả keys có pattern chat_history:*
        keys = r.keys("chat_history:*")
        logs = []
        
        for key in keys:
            session_id = key.replace("chat_history:", "")
            history = r.lrange(key, 0, -1)  # Lấy tất cả messages
            
            if history:
                messages = [json.loads(h) for h in history]
                first_msg = messages[-1]  # Message đầu tiên (oldest)
                last_msg = messages[0]   # Message cuối (newest)
                
                # Lấy session metadata
                session_key = f"session_meta:{session_id}"
                session_meta = r.hgetall(session_key)
                
                # Xác định status
                import time
                current_time = time.time()
                last_activity = float(session_meta.get("last_activity", current_time))
                stored_status = session_meta.get("status", "active")
                
                # Nếu đã completed thì giữ nguyên, nếu không thì check timeout
                if stored_status == "completed":
                    is_active = False
                else:
                    is_active = (current_time - last_activity) < 1800  # Active nếu có hoạt động trong 30 phút
                
                # Lấy thông tin từ message mới nhất
                start_time = first_msg.get("timestamp", current_time - len(messages) * 60)
                end_time = last_msg.get("timestamp", current_time)
                student_id = session_meta.get("student_id") or first_msg.get("student_id", "N/A")
                
                # Xác định agent chính được sử dụng
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
                    "last_message": last_msg.get("user", "")[:50] + "..." if len(last_msg.get("user", "")) > 50 else last_msg.get("user", ""),
                    "agent": main_agent
                })
        
        # Sắp xếp theo thời gian mới nhất
        logs.sort(key=lambda x: x["end_time"], reverse=True)
        
        return {
            "logs": logs,
            "total": len(logs)
        }
        
    except Exception as e:
        print(f"Error getting chat logs: {e}")
        return {"logs": [], "total": 0}

@app.get("/chat-logs/{session_id}")
async def get_chat_log_detail(session_id: str):
    """Lấy chi tiết một phiên chat"""
    try:
        history = get_chat_history(session_id, limit=100)
        return {
            "session_id": session_id,
            "messages": history,
            "total_messages": len(history)
        }
    except Exception as e:
        print(f"Error getting chat log detail: {e}")
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
    except Exception as e:
        print(f"Error marking session complete: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/chat-logs/{session_id}/reopen")
async def reopen_session(session_id: str):
    """Mở lại session"""
    try:
        session_key = f"session_meta:{session_id}"
        if r.exists(session_key):
            import time
            r.hset(session_key, "status", "active")
            r.hset(session_key, "last_activity", time.time())
            return {"message": "Session reopened", "session_id": session_id}
        else:
            raise HTTPException(status_code=404, detail="Session not found")
    except Exception as e:
        print(f"Error reopening session: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")