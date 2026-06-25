import uuid
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models import Flashcard, VocabularyItem
from app.services.spaced_repetition.sm2 import review

router = APIRouter(tags=["flashcards"])


@router.get("/flashcards/due")
async def get_due_flashcards(
    user_id: uuid.UUID,
    document_id: uuid.UUID | None = Query(None),
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Flashcard, VocabularyItem)
        .join(VocabularyItem, Flashcard.vocabulary_item_id == VocabularyItem.id)
        .where(Flashcard.user_id == user_id, Flashcard.next_review_date <= date.today())
    )
    if document_id:
        query = query.where(VocabularyItem.document_id == document_id)
    query = query.limit(limit)
    result = await db.execute(query)
    rows = result.all()

    return [
        {
            "flashcard_id": str(fc.id),
            "vocabulary_item_id": str(vi.id),
            "german_word": vi.german_word,
            "translation_en": vi.translation_en,
            "gender": vi.gender,
            "part_of_speech": vi.part_of_speech,
            "cefr_level": vi.cefr_level,
            "example_sentence": vi.example_sentence,
            "ease_factor": fc.ease_factor,
            "interval_days": fc.interval_days,
            "repetitions": fc.repetitions,
            "times_correct": fc.times_correct,
            "times_incorrect": fc.times_incorrect,
        }
        for fc, vi in rows
    ]


class ReviewRequest(BaseModel):
    quality: int  # 0-5


@router.post("/flashcards/{flashcard_id}/review")
async def review_flashcard(
    flashcard_id: uuid.UUID,
    req: ReviewRequest,
    db: AsyncSession = Depends(get_db),
):
    if req.quality < 0 or req.quality > 5:
        raise HTTPException(400, "quality must be between 0 and 5")

    fc = await db.get(Flashcard, flashcard_id)
    if not fc:
        raise HTTPException(404, "Flashcard not found")

    state = review(fc.ease_factor, fc.interval_days, fc.repetitions, req.quality)
    fc.ease_factor = state.ease_factor
    fc.interval_days = state.interval_days
    fc.repetitions = state.repetitions
    fc.next_review_date = state.next_review_date
    fc.last_reviewed_at = datetime.now(timezone.utc)

    if req.quality >= 3:
        fc.times_correct += 1
    else:
        fc.times_incorrect += 1

    await db.commit()
    return {
        "new_interval": state.interval_days,
        "next_review_date": state.next_review_date.isoformat(),
        "ease_factor": state.ease_factor,
    }


@router.get("/flashcards/stats")
async def get_flashcard_stats(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    due_today = await db.scalar(
        select(func.count()).where(
            Flashcard.user_id == user_id,
            Flashcard.next_review_date <= date.today(),
        )
    )
    reviewed_today = await db.scalar(
        select(func.count()).where(
            Flashcard.user_id == user_id,
            func.date(Flashcard.last_reviewed_at) == date.today(),
        )
    )
    total = await db.scalar(select(func.count()).where(Flashcard.user_id == user_id))
    return {
        "due_today": due_today or 0,
        "reviewed_today": reviewed_today or 0,
        "total": total or 0,
    }
