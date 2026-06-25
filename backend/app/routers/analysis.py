import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import VocabularyItem, GrammarPattern, Document

router = APIRouter(tags=["analysis"])


@router.get("/documents/{document_id}/vocabulary")
async def get_vocabulary(
    document_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    difficulty: int | None = Query(None),
    pos: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(VocabularyItem).where(VocabularyItem.document_id == document_id)
    if difficulty:
        query = query.where(VocabularyItem.difficulty == difficulty)
    if pos:
        query = query.where(VocabularyItem.part_of_speech == pos)
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()
    return [
        {
            "id": str(v.id),
            "german_word": v.german_word,
            "lemma": v.lemma,
            "translation_en": v.translation_en,
            "part_of_speech": v.part_of_speech,
            "gender": v.gender,
            "plural_form": v.plural_form,
            "difficulty": v.difficulty,
            "cefr_level": v.cefr_level,
            "frequency_in_doc": v.frequency_in_doc,
            "example_sentence": v.example_sentence,
        }
        for v in items
    ]


@router.get("/documents/{document_id}/grammar")
async def get_grammar(
    document_id: uuid.UUID,
    pattern_type: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(GrammarPattern).where(GrammarPattern.document_id == document_id)
    if pattern_type:
        query = query.where(GrammarPattern.pattern_type == pattern_type)
    query = query.order_by(GrammarPattern.difficulty)
    result = await db.execute(query)
    patterns = result.scalars().all()
    return [
        {
            "id": str(p.id),
            "pattern_type": p.pattern_type,
            "pattern_name": p.pattern_name,
            "explanation": p.explanation,
            "rule_summary": p.rule_summary,
            "example_from_doc": p.example_from_doc,
            "example_translation": p.example_translation,
            "difficulty": p.difficulty,
            "occurrences": p.occurrences,
        }
        for p in patterns
    ]
