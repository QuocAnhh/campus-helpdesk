from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Optional

from rag.ingest import ingest_policies as rag_ingest
from rag.retriever import retrieve_documents
from rag.rerank import rerank_documents


app = FastAPI(title="Policy Service")


class CheckBody(BaseModel):
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

    return {
        "citations": citations,
        "needs_answer": bool(citations)
    }