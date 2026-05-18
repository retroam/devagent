from pydantic import BaseModel, Field
from typing import Any, Optional

class FAQEntry(BaseModel):
    id: int
    question: str
    answer: str
    text: str 

class SearchResult(BaseModel):
    entry_id: int
    question: str
    answer: str
    score: float = Field(ge=-1.0, le=1.0)

class Answer(BaseModel):
    answer: str
    sources: list[int]
    could_answer: bool

class Trace(BaseModel):
    tool_name: str
    args: dict[str, Any]
    result_ids: list[int] = Field(default_factory=list)
    result_scores: list[float] = Field(default_factory=list)
    elapsed_ms: int
    requested_by_model: bool = True 