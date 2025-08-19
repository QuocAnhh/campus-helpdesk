from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict
from common.llm import chat

app = FastAPI(title="Escalation Service")

class SummarizeBody(BaseModel):
    ticket: Dict
    interactions: List[Dict]

@app.post("/summarize")
async def summarize(b: SummarizeBody):
    provider = os.getenv("LLM_PROVIDER", "stub").lower()
    if provider != "stub":
        # TODO: Implement LLM-based summarization
        messages = [
            {"role": "system", "content": "Summarize the following ticket interactions for an operator."},
            {"role": "user", "content": f"Ticket: {b.ticket}\nInteractions: {b.interactions}"}
        ]
        summary = chat(messages)
    else:
        # Template-based summarization
        summary = {
            "title": f"Summary for ticket {b.ticket.get('id', 'N/A')}",
            "context": "This is a summary of the ticket and its interactions.",
            "steps_done": "Initial contact made.",
            "missing_info": "User's full name and contact number.",
            "next_actions": "Contact the user to get more information."
        }
    return summary