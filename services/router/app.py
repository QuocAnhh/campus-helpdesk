from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import sys
import os

# Add common to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'common')))
from llm import chat


app = FastAPI(title="Router Service")

class RouteBody(BaseModel):
    channel: str
    text: str
    student_id: Optional[str] = None


@app.post("/classify")
async def classify(b: RouteBody):
    # TODO: route to appropriate service
    t = b.text.lower()
    if "mật khẩu" in t or "mat khau" in t:
        label = "it.reset_password"
    elif "rút môn" in t or "rut mon" in t:
        label = "hocvu.withdraw_course"
    elif "ký túc" in t or "ky tuc" in t:
        label = "kytuc.report_issue"
    else:
        label = "general.faq"
    return {"label": label, "confidence": 0.75, "entities": {}}


@app.post("/classify_llm")
async def classify_llm(b: RouteBody):
    # TODO: load prompt from file
    messages = [
        {"role": "system", "content": "Bạn là bộ phân loại intent cho trợ lý Helpdesk trường đại học..."},
        {"role": "user", "content": b.text}
    ]
    response = chat(messages)
    return response

    