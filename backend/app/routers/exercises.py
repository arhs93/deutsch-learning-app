import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import Exercise, ExerciseAttempt, User, Flashcard
from app.services.gamification.xp_calculator import xp_for_attempt, level_for_xp
from app.services.gamification.achievement_checker import check_and_award

router = APIRouter(tags=["exercises"])


@router.get("/exercises")
async def list_exercises(
    document_id: uuid.UUID,
    exercise_type: str | None = Query(None),
    difficulty: int | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = select(Exercise).where(Exercise.document_id == document_id)
    if exercise_type:
        query = query.where(Exercise.exercise_type == exercise_type)
    if difficulty:
        query = query.where(Exercise.difficulty == difficulty)
    query = query.limit(limit)
    result = await db.execute(query)
    exercises = result.scalars().all()
    return [
        {
            "id": str(e.id),
            "exercise_type": e.exercise_type,
            "prompt": e.prompt,
            "correct_answer": e.correct_answer,
            "distractors": e.distractors,
            "hint": e.hint,
            "difficulty": e.difficulty,
        }
        for e in exercises
    ]


class AttemptRequest(BaseModel):
    exercise_id: uuid.UUID
    user_id: uuid.UUID
    user_answer: str
    time_spent_ms: int | None = None


@router.post("/exercises/attempt")
async def submit_attempt(req: AttemptRequest, db: AsyncSession = Depends(get_db)):
    exercise = await db.get(Exercise, req.exercise_id)
    if not exercise:
        raise HTTPException(404, "Exercise not found")

    is_correct = req.user_answer.strip().lower() == exercise.correct_answer.strip().lower()
    xp = xp_for_attempt(exercise.exercise_type, is_correct)

    attempt = ExerciseAttempt(
        user_id=req.user_id,
        exercise_id=req.exercise_id,
        user_answer=req.user_answer,
        is_correct=is_correct,
        time_spent_ms=req.time_spent_ms,
        xp_earned=xp,
    )
    db.add(attempt)

    user = await db.get(User, req.user_id)
    if user:
        user.total_xp += xp
        old_level = user.current_level
        user.current_level = level_for_xp(user.total_xp)
        level_up = user.current_level > old_level

        today = date.today()
        if user.last_active_date is None or user.last_active_date < today:
            from datetime import timedelta
            if user.last_active_date == today - timedelta(days=1):
                user.streak_days += 1
            elif user.last_active_date != today:
                user.streak_days = 1
            user.last_active_date = today
            if user.streak_days > user.longest_streak:
                user.longest_streak = user.streak_days
    else:
        level_up = False

    await db.flush()
    new_achievements = await check_and_award(req.user_id, db)
    await db.commit()

    return {
        "is_correct": is_correct,
        "correct_answer": exercise.correct_answer,
        "explanation": exercise.explanation,
        "xp_earned": xp,
        "level_up": level_up,
        "achievements_unlocked": new_achievements,
    }
