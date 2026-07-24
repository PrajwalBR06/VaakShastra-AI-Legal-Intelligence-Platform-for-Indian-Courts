"""
Pydantic schemas for request/response validation.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


# ============ Auth Schemas ============

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


# ============ Document Schemas ============

class DocumentResponse(BaseModel):
    id: str
    original_filename: str
    file_size_bytes: int
    mime_type: str
    page_count: Optional[int]
    word_count: Optional[int]
    storage_backend: str
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int
    page: int
    per_page: int


# ============ Analysis Schemas ============

class AnalysisRequest(BaseModel):
    document_id: Optional[str] = None
    text: Optional[str] = Field(None, max_length=50000)
    language: str = Field(default="English")
    depth: str = Field(default="standard")


class AnalysisResponse(BaseModel):
    id: str
    document_id: Optional[str] = None
    status: str
    language: str
    depth: str
    summary: Optional[str] = None
    key_facts: Optional[str] = None
    ipc_sections: Optional[str] = None
    verdict_prediction: Optional[str] = None
    confidence_score: Optional[float] = None
    reasoning: Optional[str] = None
    similar_cases: Optional[str] = None
    processing_time_ms: Optional[int] = None
    model_used: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AnalysisListResponse(BaseModel):
    analyses: List[AnalysisResponse]
    total: int
