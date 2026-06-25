import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import User, UserDocumentProgress, LearningSession, Document
from app.services.gamification.xp_calculator import level_for_xp, xp_to_next_level

router = APIRouter(tags=["progress"])


async def _get_or_create_user(user_id: uuid.UUID, db: AsyncSession) -> User:
    user = await db.get(User, user_id)
    if not user:
        user = User(id=user_id, email=f"{user_id}@demo.local")
        db.add(user)
        await db.commit()
    return user


@router.get("/progress")
async def get_progress(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    user = await _get_or_create_user(user_id, db)

    progress_rows = await db.execute(
        select(UserDocumentProgress, Document)
        .join(Document, UserDocumentProgress.document_id == Document.id)
        .where(UserDocumentProgress.user_id == user_id)
    )
    doc_progress = [
        {
            "document_id": str(p.document_id),
            "document_title": d.title,
            "vocabulary_mastered": p.vocabulary_mastered,
            "vocabulary_total": p.vocabulary_total,
            "exercises_completed": p.exercises_completed,
            "completion_percentage": p.completion_percentage,
        }
        for p, d in progress_rows.all()
    ]

    return {
        "level": user.current_level,
        "total_xp": user.total_xp,
        "xp_to_next_level": xp_to_next_level(user.total_xp),
        "streak_days": user.streak_days,
        "longest_streak": user.longest_streak,
        "documents": doc_progress,
    }


class SessionStartRequest(BaseModel):
    user_id: uuid.UUID
    document_id: uuid.UUID | None = None
    session_type: str | None = None


@router.post("/sessions/start")
async def start_session(req: SessionStartRequest, db: AsyncSession = Depends(get_db)):
    session = LearningSession(
        user_id=req.user_id,
        document_id=req.document_id,
        session_type=req.session_type,
    )
    db.add(session)
    await db.commit()
    return {"session_id": str(session.id)}


class SessionEndRequest(BaseModel):
    exercises_done: int = 0
    accuracy_pct: float | None = None


@router.post("/sessions/{session_id}/end")
async def end_session(
    session_id: uuid.UUID,
    req: SessionEndRequest,
    db: AsyncSession = Depends(get_db),
):
    session = await db.get(LearningSession, session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    session.ended_at = datetime.now(timezone.utc)
    session.exercises_done = req.exercises_done
    session.accuracy_pct = req.accuracy_pct
    if session.started_at:
        delta = session.ended_at - session.started_at
        session.duration_seconds = int(delta.total_seconds())

    from app.services.gamification.xp_calculator import SESSION_COMPLETION_BONUS
    bonus = SESSION_COMPLETION_BONUS if req.exercises_done > 0 else 0
    session.xp_earned = bonus

    user = await db.get(User, session.user_id)
    level_up = False
    if user and bonus > 0:
        user.total_xp += bonus
        old_level = user.current_level
        user.current_level = level_for_xp(user.total_xp)
        level_up = user.current_level > old_level

    from app.services.gamification.achievement_checker import check_and_award
    speed_demon = (
        req.exercises_done >= 10
        and session.duration_seconds is not None
        and session.duration_seconds <= 300
    )
    new_achievements = await check_and_award(
        session.user_id, db, extra={"exercises_done": req.exercises_done, "speed_demon": speed_demon}
    )
    await db.commit()

    return {
        "xp_earned": bonus,
        "level_up": level_up,
        "achievements_unlocked": new_achievements,
        "duration_seconds": session.duration_seconds,
    }
