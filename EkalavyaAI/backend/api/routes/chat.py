"""
EkalavyaAI — Chat API Routes
Real-time doubt solving with SSE streaming + persistent chat history.
"""
import json
import logging
import uuid as _uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, validator

from api.dependencies import get_current_user, check_plan_limit
from agents.orchestrator import get_orchestrator

logger = logging.getLogger(__name__)
router = APIRouter()


class ChatMessageRequest(BaseModel):
    message: str
    exam: str
    chapter_id: Optional[str] = None
    session_id: Optional[str] = None

    @validator("message")
    def message_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Message cannot be empty")
        if len(v) > 2000:
            raise ValueError("Message too long (max 2000 characters)")
        return v

    @validator("exam")
    def valid_exam(cls, v: str) -> str:
        valid = {"CA_FOUNDATION", "CA_INTERMEDIATE", "CA_FINAL", "JEE", "NEET"}
        if v not in valid:
            raise ValueError(f"Invalid exam. Must be one of: {valid}")
        return v


@router.post("/message")
async def send_message(
    request: ChatMessageRequest,
    current_user=Depends(get_current_user),
):
    """
    Send a doubt/question and receive streamed AI response via SSE.
    Uses Teacher Agent (Claude 3.5 Sonnet) for exam-quality answers.
    """
    await check_plan_limit(current_user, "general_chat")

    orchestrator = get_orchestrator()
    student_id = str(current_user.id)
    session_id = request.session_id or str(_uuid.uuid4())[:8]

    # Persist user message
    await _save_message(student_id, session_id, "user", request.message, request.exam)

    async def event_stream():
        full_response = ""
        try:
            yield _sse("start", {"session_id": session_id})

            async for chunk in orchestrator.solve_question(
                student_id=student_id,
                question=request.message,
                exam=request.exam,
                chapter_id=request.chapter_id,
            ):
                ctype = chunk.get("type")
                content = chunk.get("content", "")
                if ctype == "text" and content:
                    full_response += content
                    yield _sse("chunk", {"content": content, "session_id": session_id})
                elif ctype == "complete":
                    yield _sse("complete", {**chunk, "session_id": session_id})

        except Exception as e:
            logger.error(f"Chat stream error for user {student_id}: {e}", exc_info=True)
            yield _sse("error", {"message": "Something went wrong. Please try again."})
        finally:
            if full_response:
                await _save_message(student_id, session_id, "assistant", full_response, request.exam)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.get("/history")
async def get_chat_history(
    session_id: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    current_user=Depends(get_current_user),
):
    """Get chat history for the student (optionally filtered by session)."""
    try:
        from sqlalchemy import select
        from models.user import ChatMessage
        from models.database import get_async_session

        async with get_async_session() as session:
            query = (
                select(ChatMessage)
                .where(ChatMessage.student_id == current_user.id)
                .order_by(ChatMessage.created_at.desc())
                .limit(limit)
            )
            if session_id:
                query = query.where(ChatMessage.session_id == session_id)

            result = await session.execute(query)
            messages = result.scalars().all()

            return {
                "messages": [
                    {
                        "id": str(m.id),
                        "session_id": m.session_id,
                        "role": m.role,
                        "content": m.content,
                        "exam": m.exam,
                        "created_at": m.created_at.isoformat(),
                    }
                    for m in reversed(messages)
                ],
                "total": len(messages),
            }
    except Exception as e:
        logger.error(f"Chat history error: {e}")
        raise HTTPException(status_code=500, detail="Failed to load chat history")


@router.get("/sessions")
async def list_sessions(
    limit: int = Query(20, le=50),
    current_user=Depends(get_current_user),
):
    """List distinct chat sessions for the student."""
    try:
        from sqlalchemy import select, func, distinct
        from models.user import ChatMessage
        from models.database import get_async_session

        async with get_async_session() as session:
            result = await session.execute(
                select(
                    ChatMessage.session_id,
                    func.count(ChatMessage.id).label("message_count"),
                    func.max(ChatMessage.created_at).label("last_message"),
                )
                .where(ChatMessage.student_id == current_user.id)
                .group_by(ChatMessage.session_id)
                .order_by(func.max(ChatMessage.created_at).desc())
                .limit(limit)
            )
            rows = result.all()
            return {
                "sessions": [
                    {
                        "session_id": row.session_id,
                        "message_count": row.message_count,
                        "last_message": row.last_message.isoformat(),
                    }
                    for row in rows
                ]
            }
    except Exception as e:
        logger.error(f"List sessions error: {e}")
        return {"sessions": []}


@router.delete("/session/{session_id}")
async def clear_session(
    session_id: str,
    current_user=Depends(get_current_user),
):
    """Delete all messages in a specific chat session."""
    try:
        from sqlalchemy import delete
        from models.user import ChatMessage
        from models.database import get_async_session

        async with get_async_session() as session:
            await session.execute(
                delete(ChatMessage).where(
                    ChatMessage.student_id == current_user.id,
                    ChatMessage.session_id == session_id,
                )
            )
            await session.commit()
        return {"message": "Session cleared", "session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Helpers ─────────────────────────────────────────────────────────────────
def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def _save_message(
    student_id: str, session_id: str, role: str, content: str, exam: str = "CA_FOUNDATION"
) -> None:
    """Persist chat message to PostgreSQL (non-critical)."""
    try:
        from models.user import ChatMessage
        from models.database import get_async_session
        import uuid as _uuid

        async with get_async_session() as session:
            msg = ChatMessage(
                student_id=_uuid.UUID(student_id),
                session_id=session_id,
                role=role,
                content=content[:4000],   # Truncate very long AI responses
                exam=exam,
            )
            session.add(msg)
            await session.commit()
    except Exception as e:
        logger.warning(f"Failed to persist chat message: {e}")
