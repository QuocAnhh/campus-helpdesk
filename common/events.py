from __future__ import annotations
from pydantic import BaseModel
from typing import Optional, List, Dict


class Ingested(BaseModel):
    request_id: str
    interaction: Dict


class Routed(BaseModel):
    request_id: str
    intent: Dict


class AnswerReady(BaseModel):
    request_id: str
    answer: Dict