"""
SQLAlchemy ORM models - uses String IDs for SQLite compatibility.
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Text, Boolean,
    DateTime, ForeignKey
)
from sqlalchemy.orm import relationship
from app.database import Base


def generate_uuid():
    return uuid.uuid4().hex


class User(Base):
    __tablename__ = "users"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    documents = relationship("Document", back_populates="owner", cascade="all, delete-orphan")
    analyses = relationship("Analysis", back_populates="user", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    user_id = Column(String(32), ForeignKey("users.id"), nullable=False)
    original_filename = Column(String(512), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    page_count = Column(Integer, nullable=True)
    word_count = Column(Integer, nullable=True)
    storage_backend = Column(String(10), default="local")
    storage_path = Column(String(1024), nullable=False)
    extracted_text = Column(Text, nullable=True)
    extraction_method = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)

    owner = relationship("User", back_populates="documents")
    analyses = relationship("Analysis", back_populates="document", cascade="all, delete-orphan")


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    user_id = Column(String(32), ForeignKey("users.id"), nullable=False)
    document_id = Column(String(32), ForeignKey("documents.id"), nullable=True)
    language = Column(String(20), default="English")
    depth = Column(String(20), default="standard")
    status = Column(String(20), default="pending")
    error_message = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    key_facts = Column(Text, nullable=True)
    ipc_sections = Column(Text, nullable=True)
    verdict_prediction = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True)
    reasoning = Column(Text, nullable=True)
    similar_cases = Column(Text, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    model_used = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="analyses")
    document = relationship("Document", back_populates="analyses")


class AnalysisReport(Base):
    __tablename__ = "reports"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    analysis_id = Column(String(32), ForeignKey("analyses.id"), nullable=False)
    format = Column(String(10), default="txt")
    storage_path = Column(String(1024), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
