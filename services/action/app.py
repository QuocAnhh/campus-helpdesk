from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict

from .toolspec import TOOL_SCHEMAS

app = FastAPI(title="Action Service")

class ToolCallBody(BaseModel):
    tool_name: str
    tool_args: Dict

@app.post("/call_tool")
async def call_tool(b: ToolCallBody):
    if b.tool_name not in TOOL_SCHEMAS:
        raise HTTPException(status_code=404, detail="Tool not found")

    # TODO: Validate tool_args against the schema

    # Route to stub functions
    if b.tool_name == "reset_password":
        return reset_password_stub(b.tool_args)
    elif b.tool_name == "create_glpi_ticket":
        return create_glpi_ticket_stub(b.tool_args)
    elif b.tool_name == "request_dorm_fix":
        return request_dorm_fix_stub(b.tool_args)
    elif b.tool_name == "book_room":
        return book_room_stub(b.tool_args)
    else:
        raise HTTPException(status_code=404, detail="Tool not found")

# Stub functions
def reset_password_stub(args: Dict):
    print(f"Called reset_password with args: {args}")
    return {"status": "success", "message": "Password reset link sent."}

def create_glpi_ticket_stub(args: Dict):
    print(f"Called create_glpi_ticket with args: {args}")
    return {"status": "success", "ticket_id": "12345"}

def request_dorm_fix_stub(args: Dict):
    print(f"Called request_dorm_fix with args: {args}")
    return {"status": "success", "request_id": "abcde"}

def book_room_stub(args: Dict):
    print(f"Called book_room with args: {args}")
    return {"status": "success", "booking_id": "xyz-789"}