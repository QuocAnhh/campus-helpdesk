from fastapi import FastAPI
from pydantic import BaseModel
import redis
import os
import httpx
from typing import Optional

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
r = redis.from_url(REDIS_URL, decode_responses=True)
ROUTER_URL = os.getenv("ROUTER_URL", "http://localhost:8001") # Assuming router runs on 8001
ANSWER_URL = os.getenv("ANSWER_URL", "http://localhost:8002") # Assuming answer runs on 8002

app = FastAPI(title="Monolith Service")

class AskBody(BaseModel):
    channel: str
    text: str
    student_id: Optional[str] = None

@app.post("/ask")
async def ask(b: AskBody):
    # Route to appropriate service
    async with httpx.AsyncClient() as client:
        router_response = await client.post(f"{ROUTER_URL}/classify", json={"channel": b.channel, "text": b.text})
        router_response.raise_for_status()
        router_result = router_response.json()
        label = router_result.get("label")

        intent_data = {"label": label}
        answer_response = await client.post(f"{ANSWER_URL}/compose", json={"intent": intent_data, "channel": b.channel})
        answer_response.raise_for_status()
        answer_result = answer_response.json()

    r.lpush("tickets", f"{label}:{b.text}")
    return {"intent": label, "answer": answer_result}

@app.get("/tickets")
async def tickets():
    items = r.lrange("tickets", 0, 50)
    return {"count": len(items), "items": items}