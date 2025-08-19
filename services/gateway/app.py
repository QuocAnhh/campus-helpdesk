from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
import os
import uuid
import json
from redis import Redis
from agents import AgentManager

# --- Setup ---
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
r = Redis.from_url(REDIS_URL, decode_responses=True)

app = FastAPI(title="Campus Helpdesk Gateway")

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Initialize Agent Manager ---
agent_manager = AgentManager()

# --- Chat History Management ---
def get_chat_history(session_id: str, limit: int = 10) -> List[Dict]:
    if not session_id:
        return []
    key = f"chat_history:{session_id}"
    history = r.lrange(key, 0, limit - 1)
    return [json.loads(h) for h in reversed(history)]

def add_to_chat_history(session_id: str, user_message: str, bot_message: str):
    if not session_id:
        return
    key = f"chat_history:{session_id}"
    turn = {"user": user_message, "bot": bot_message}
    r.lpush(key, json.dumps(turn))
    r.ltrim(key, 0, 99)

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
        add_to_chat_history(body.session_id, body.text, final_reply)
        
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