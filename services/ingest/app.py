from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, Dict

app = FastAPI(title="Ingest Service")

class IngestBody(BaseModel):
    channel: str
    text: str
    student_id: Optional[str] = None
    meta: Dict[str, str] = {}

@app.post("/ingest")
async def ingest(b: IngestBody):
    # TODO: normalize text, redact PII, push to event bus
    return {"ok": True, "normalized": b.model_dump()}