"""
Analysis routes - trigger AI analysis on documents.
"""

import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import User, Document, Analysis
from app.schemas import AnalysisRequest, AnalysisResponse, AnalysisListResponse
from app.services.auth import get_current_user
from app.services.llm_service import llm_service
from app.models import generate_uuid

router = APIRouter(prefix="/analysis", tags=["Analysis"])


@router.post("/", response_model=AnalysisResponse, status_code=status.HTTP_201_CREATED)
async def create_analysis(
    request: AnalysisRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    text = ""
    document_id = None

    if request.document_id:
        result = await db.execute(
            select(Document).where(
                Document.id == request.document_id,
                Document.user_id == current_user.id,
                Document.is_deleted == 0,
            )
        )
        document = result.scalar_one_or_none()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        text = document.extracted_text or ""
        document_id = document.id
    elif request.text:
        text = request.text
    else:
        raise HTTPException(status_code=400, detail="Provide either document_id or text")

    if len(text.strip()) < 50:
        raise HTTPException(status_code=400, detail="Text too short for analysis (min 50 chars)")

    # Create analysis record
    analysis = Analysis(
        id=generate_uuid(),
        user_id=current_user.id,
        document_id=document_id,
        language=request.language,
        depth=request.depth,
        status="processing",
    )
    db.add(analysis)
    await db.commit()

    try:
        # Step 1: Retrieve similar cases
        similar_cases = await llm_service.retrieve_similar_cases(text)

        # Step 2: Run analysis
        result = await llm_service.analyze_document(
            text=text,
            similar_cases=similar_cases,
            language=request.language,
            depth=request.depth,
        )

        # Step 3: Save results (convert everything to strings for SQLite)
        analysis.status = "completed"
        analysis.summary = str(result.get("summary", ""))
        analysis.key_facts = str(result.get("key_facts", ""))
        analysis.ipc_sections = str(result.get("ipc_sections", ""))
        analysis.verdict_prediction = str(result.get("verdict_prediction", ""))
        analysis.confidence_score = float(result.get("confidence", 0))
        analysis.reasoning = str(result.get("reasoning", ""))
        analysis.similar_cases = json.dumps(similar_cases) if similar_cases else "[]"
        analysis.processing_time_ms = result.get("processing_time_ms")
        analysis.tokens_used = result.get("tokens_used")
        analysis.model_used = result.get("model_used")
        analysis.completed_at = datetime.utcnow()

        await db.commit()
        await db.refresh(analysis)

    except Exception as e:
        await db.rollback()
        # Update status to failed
        analysis.status = "failed"
        analysis.error_message = str(e)
        db.add(analysis)
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    return analysis


@router.get("/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(
    analysis_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Analysis).where(Analysis.id == analysis_id, Analysis.user_id == current_user.id)
    )
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis


@router.get("/", response_model=AnalysisListResponse)
async def list_analyses(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Analysis).where(Analysis.user_id == current_user.id).order_by(Analysis.created_at.desc()).limit(50)
    )
    analyses = result.scalars().all()
    return AnalysisListResponse(analyses=analyses, total=len(analyses))
