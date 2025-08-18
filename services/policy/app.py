from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Optional

from .rag.ingest import ingest_policies as rag_ingest
from .rag.retriever import retrieve_documents
from .rag.rerank import rerank_documents


app = FastAPI(title="Policy Service")


class CheckBody(BaseModel):
    intent: Dict
    text: str

class RagBody(BaseModel):
    text: str


@app.post("/ingest_policies")
async def ingest_policies():
    # TODO: Add authentication to this endpoint
    return rag_ingest()

@app.post("/rag_answer")
async def rag_answer(b: RagBody):
    retrieved = retrieve_documents(b.text)
    reranked = rerank_documents(retrieved)
    # TODO: Call LLM to generate answer based on reranked docs
    return {"citations": reranked, "answer": "..."}

@app.post("/check")
async def check(b: CheckBody):
    # RAG-based check
    retrieved = retrieve_documents(b.text)
    citations = rerank_documents(retrieved)

    # Simple rule-based check as a fallback
    if not citations:
        label = b.intent.get("label", "")
        if label == "it.reset_password":
            citations = [{
                "doc": "Quy định CNTT",
                "section": "2.1",
                "quote": "Sinh viên phải xác thực hai bước trước khi đặt lại mật khẩu",
                "url": None
            }]
        elif label == "hocvu.withdraw_course":
            citations = [{
                "doc": "Quy chế đào tạo",
                "section": "Điều 3.2",
                "quote": "Sinh viên có quyền rút môn học trong vòng 1 tuần kể từ khi bắt đầu học",
                "url": None
            }]
        elif label == "kytuc.report_issue":
            citations = [{
                "doc": "Quy chế ký túc xá",
                "section": "Điều 4.1",
                "quote": "Sinh viên có quyền báo cáo vấn đề kỹ thuật trong ký túc xá",
                "url": None
            }]

    return {
        "citations": citations,
        "needs_answer": bool(citations)
    }