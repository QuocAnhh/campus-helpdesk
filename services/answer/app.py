from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict
import sys
import os

# Add common to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'common')))
from llm import chat

app = FastAPI(title="Answer Composer")

class ComposeBody(BaseModel):
    intent: Dict
    citations: List[Dict] = []
    channel: str

@app.post("/compose")
async def compose(b: ComposeBody):
    label = b.intent.get("label", "general.faq")
    suggested_tool_call = None

    if label == "it.reset_password":
        reply = (
            "Mình có thể giúp bạn đặt lại mật khẩu SSO. "
            "Bạn có muốn mình gửi yêu cầu đặt lại mật khẩu không?"
        )
        citations = b.citations
        suggested_tool_call = {
            "tool_name": "reset_password",
            "tool_args": {"student_id": b.intent.get("student_id")}
        }
    elif label == "hocvu.withdraw_course":
        reply = (
            "ℹRút học phần sau thời hạn cần phê duyệt. "
            "Mình đã tạo yêu cầu, bạn bổ sung lý do và minh chứng nhé."
        )
        citations = b.citations
    elif label == "kytuc.report_issue":
        reply = "Báo cáo vấn đề kỹ thuật trong ký túc xá"
        citations = b.citations
    else:
        reply = "Mình đã ghi nhận yêu cầu và sẽ phản hồi sớm nhất."
        citations = b.citations
    return {"reply": reply, "citations": citations, "suggested_tool_call": suggested_tool_call}

@app.post("/compose_llm")
async def compose_llm(b: ComposeBody):
    # TODO: load prompt from file
    # TODO: format citations for prompt
    messages = [
        {"role": "system", "content": "Bạn là Answer Composer. Tạo câu trả lời ngắn gọn, lịch sự, có bullet..."},
        {"role": "user", "content": f"Intent: {b.intent.get('label')}\nCitations: {b.citations}"}
    ]
    response = chat(messages)
    # TODO: parse LLM response to see if it suggests a tool call
    return {"reply": response, "citations": b.citations}