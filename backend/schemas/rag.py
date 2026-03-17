from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4

class DocumentChunk(BaseModel):
    chunk_id: str = Field(default_factory=lambda: str(uuid4()))
    doc_id: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class RagQuery(BaseModel):
    question: str
    history: Optional[List[Dict[str, str]]] = None # For future multi-turn

class RagResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
