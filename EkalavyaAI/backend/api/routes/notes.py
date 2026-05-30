"""
EkalavyaAI — Notes API Routes
Handles notes generation, retrieval, download with SSE streaming.
"""
import json
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from api.dependencies import get_current_user, check_plan_limit
from agents.orchestrator import get_orchestrator
from services.cache_service import CacheService
from models.database import get_async_session
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter()
cache_service = CacheService()


# ─── Request/Response Schemas ────────────────────────────────────────────────
class GenerateNotesRequest(BaseModel):
    exam: str
    subject: str
    chapter_id: str
    chapter_name: str
    language: str = "English"


class NoteResponse(BaseModel):
    id: str
    chapter_name: str
    exam: str
    subject: str
    language: str
    pdf_url: Optional[str]
    docx_url: Optional[str]
    quality_score: float
    from_cache: bool
    created_at: str


# ─── Routes ──────────────────────────────────────────────────────────────────
@router.post("/generate")
async def generate_notes(
    request: GenerateNotesRequest,
    current_user=Depends(get_current_user),
):
    """
    Generate premium chapter notes with SSE streaming.

    Returns a Server-Sent Events stream with:
    - progress: agent progress updates
    - chunk: notes content chunks
    - complete: final PDF/DOCX URLs
    """
    # Check plan limits
    await check_plan_limit(current_user, "chapter_explanations")

    orchestrator = get_orchestrator()
    student_id = str(current_user.id)

    async def event_stream():
        last_complete_chunk: dict = {}
        try:
            # Send start event
            yield _sse_event("start", {
                "message": f"Generating notes for {request.chapter_name}...",
                "exam": request.exam,
            })

            step = 0
            steps = [
                "Reading your profile...",
                "Analyzing syllabus structure...",
                "Retrieving verified content...",
                "Analyzing past year patterns...",
                "Your teacher is writing notes...",
                "Formatting premium notes...",
                "Generating diagrams...",
                "Quality checking...",
                "Creating PDF...",
            ]

            async for chunk in orchestrator.generate_notes(
                student_id=student_id,
                exam=request.exam,
                subject=request.subject,
                chapter_id=request.chapter_id,
                chapter_name=request.chapter_name,
                language=request.language,
            ):
                chunk_type = chunk.get("type")

                if chunk_type == "complete":
                    yield _sse_event("complete", chunk)
                elif chunk_type == "text":
                    yield _sse_event("chunk", {"content": chunk.get("content", "")})
                elif chunk_type == "progress":
                    if step < len(steps):
                        yield _sse_event("progress", {
                            "step": step + 1,
                            "total": len(steps),
                            "message": steps[step],
                        })
                        step += 1

            # Save note to DB
            await _save_note_to_db(
                student_id=student_id,
                request=request,
                chunk=last_complete_chunk,
            )

        except Exception as e:
            logger.error(f"Notes generation error for user {student_id}: {e}")
            yield _sse_event("error", {
                "message": "An error occurred. Please try again.",
                "code": "GENERATION_FAILED"
            })

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/")
async def list_notes(
    exam: Optional[str] = Query(None),
    subject: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=50),
    current_user=Depends(get_current_user),
):
    """List student's generated notes."""
    try:
        from sqlalchemy import select
        from models.user import Note, Chapter

        async with get_async_session() as session:
            query = (
                select(Note, Chapter)
                .join(Chapter, Note.chapter_id == Chapter.id)
                .where(Note.student_id == current_user.id)
                .order_by(Note.created_at.desc())
                .offset((page - 1) * limit)
                .limit(limit)
            )

            if exam:
                query = query.where(Chapter.exam == exam)
            if subject:
                query = query.where(Chapter.subject == subject)

            result = await session.execute(query)
            rows = result.all()

            return {
                "notes": [
                    {
                        "id": str(note.id),
                        "chapter_name": chapter.name,
                        "exam": chapter.exam.value,
                        "subject": chapter.subject,
                        "language": note.language.value,
                        "pdf_url": note.pdf_url,
                        "quality_score": note.quality_score,
                        "from_cache": note.from_master_cache,
                        "created_at": note.created_at.isoformat(),
                    }
                    for note, chapter in rows
                ],
                "page": page,
                "has_more": len(rows) == limit,
            }
    except Exception as e:
        logger.error(f"List notes error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve notes")


@router.get("/{note_id}")
async def get_note(
    note_id: str,
    current_user=Depends(get_current_user),
):
    """Get a specific note by ID."""
    try:
        from sqlalchemy import select
        from models.user import Note

        async with get_async_session() as session:
            result = await session.execute(
                select(Note).where(
                    Note.id == uuid.UUID(note_id),
                    Note.student_id == current_user.id,
                )
            )
            note = result.scalar_one_or_none()
            if not note:
                raise HTTPException(status_code=404, detail="Note not found")

            return {
                "id": str(note.id),
                "content": note.content_json,
                "pdf_url": note.pdf_url,
                "docx_url": note.docx_url,
                "quality_score": note.quality_score,
                "confidence_score": note.confidence_score,
                "from_cache": note.from_master_cache,
                "created_at": note.created_at.isoformat(),
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{note_id}/pdf")
async def download_pdf(
    note_id: str,
    current_user=Depends(get_current_user),
):
    """Get PDF download URL for a note."""
    await check_plan_limit(current_user, "notes_download")

    from sqlalchemy import select
    from models.user import Note

    async with get_async_session() as session:
        result = await session.execute(
            select(Note).where(
                Note.id == uuid.UUID(note_id),
                Note.student_id == current_user.id,
            )
        )
        note = result.scalar_one_or_none()
        if not note or not note.pdf_url:
            raise HTTPException(status_code=404, detail="PDF not available")

        return {"pdf_url": note.pdf_url, "expires_in": 3600}


@router.get("/cache/{cache_key}")
async def check_cache(cache_key: str):
    """Check if a master cache entry exists (public endpoint for UX)."""
    cached = await cache_service.get_master_cache(cache_key)
    return {
        "cached": cached is not None,
        "quality_score": cached.get("quality_score") if cached else None,
        "expert_verified": cached.get("expert_verified") if cached else None,
    }


# ─── Helpers ─────────────────────────────────────────────────────────────────
def _sse_event(event_type: str, data: dict) -> str:
    """Format SSE event string."""
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


async def _save_note_to_db(student_id: str, request, chunk: dict):
    """Save generated note metadata to database."""
    try:
        from models.user import Note
        from models.user import Language

        async with get_async_session() as session:
            note = Note(
                student_id=uuid.UUID(student_id),
                chapter_id=uuid.UUID(request.chapter_id),
                language=Language(request.language),
                pdf_url=chunk.get("pdf_url"),
                docx_url=chunk.get("docx_url"),
                quality_score=chunk.get("confidence", 0.8),
                confidence_score=chunk.get("confidence", 0.8),
                from_master_cache=chunk.get("from_cache", False),
                cached=chunk.get("from_cache", False),
            )
            session.add(note)
            await session.commit()
    except Exception as e:
        logger.error(f"Failed to save note to DB: {e}")
