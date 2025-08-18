from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, List, Dict
import os
import uuid
import httpx
from redis import Redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
r = Redis.from_url(REDIS_URL, decode_responses=True)

ROUTER_URL = os.getenv("ROUTER_URL", "http://localhost:8000")
POLICY_URL = os.getenv("POLICY_URL", "http://localhost:8000")
ANSWER_URL = os.getenv("ANSWER_URL", "http://localhost:8000")
TICKET_URL = os.getenv("TICKET_URL", "http://localhost:8000")


app = FastAPI()

class AskBody(BaseModel):
    channel: str
    text: str
    student_id: str | None = None


@app.post("/ask")
async def ask(body: AskBody, use_llm: bool = False):
    req_id = str(uuid.uuid4())
    async with httpx.AsyncClient(timeout=10.0) as client:
        # 1) Route intent
        classify_endpoint = "/classify_llm" if use_llm else "/classify"
        route = await client.post(f"{ROUTER_URL}{classify_endpoint}", json=body.model_dump())
        route.raise_for_status()
        intent = route.json()

        # 2) Policy/citation (optional per intent)
        pol = await client.post(f"{POLICY_URL}/check", json={
            "intent": intent,
            "text": body.text
        })
        pol.raise_for_status()
        policy_res = pol.json()
        citations = policy_res.get("citations", [])

        # 3) Compose answer
        compose_endpoint = "/compose_llm" if use_llm else "/compose"
        ans = await client.post(f"{ANSWER_URL}{compose_endpoint}", json={
            "intent": intent,
            "citations": citations,
            "channel": body.channel,
            "student_id": body.student_id
        })
        ans.raise_for_status()
        answer = ans.json()

        # 4) Create/merge ticket
        await client.post(f"{TICKET_URL}/ticket", json={
            "subject": intent.get("label", "helpdesk"),
            "category": intent.get("label", "general"),
            "priority": "normal",
            "content": {
                "student_id": body.student_id,
                "text": body.text,
                "answer": answer
            }
        })

    # cache last answer
    r.setex(f"answer:{req_id}", 300, str(answer))
    
    response = {"request_id": req_id, "answer": answer}
    
    # Handle suggested tool calls
    if "suggested_tool_call" in answer and answer["suggested_tool_call"]:
        if intent.get("label") in ["it.reset_password", "kytuc.report_issue"]:
             response["suggested_tool_call"] = answer["suggested_tool_call"]

    return response


@app.get("/tickets")
async def tickets():
    # demo: pull from Redis log if exists in ticket service, else stub
    return {"tickets": "See ticket service at /status"}