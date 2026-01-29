from pydantic import BaseModel, Field
from typing import Optional, Any, Dict, List

class IngestRequest(BaseModel):
    type: str = Field(..., description="youtube|article|audio|text")
    source_url: Optional[str] = None
    text: Optional[str] = None

class IngestResponse(BaseModel):
    media_id: str

class Lens(BaseModel):
    id: str
    name: str
    description: Optional[str] = None

class RunResponse(BaseModel):
    run_id: str

class RunStatus(BaseModel):
    id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class Media(BaseModel):
    id: str
    type: str
    source_url: Optional[str] = None
    title: Optional[str] = None
    duration_sec: Optional[int] = None
    status: str
