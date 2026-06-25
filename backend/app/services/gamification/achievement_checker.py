import uuid
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models import User, Achievement, UserAchievement, Document, VocabularyItem, GrammarPattern

logger = logging.getLogger(__name__)

ACHIEVEMENT_CONDITIONS = {
    "first_document": lambda stats: stats["documents_uploaded"] >= 1,
    "first_exercise": lambda stats: stats["exercises_completed"] >= 1,
    "streak_3": lambda stats: stats["streak_days"] >= 3,
    "streak_7": lambda stats: stats["streak_days"] >= 7,
    "streak_30": lambda stats: stats["streak_days"] >= 30,
    "vocab_50": lambda stats: stats["vocab_mastered"] >= 50,
    "vocab_100": lambda stats: stats["vocab_mastered"] >= 100,
    "level_5": lambda stats: stats["current_level"] >= 5,
    "grammar_hunter": lambda stats: stats["grammar_patterns"] >= 10,
    "polyglot": lambda stats: stats["documents_uploaded"] >= 5,
    "speed_demon": lambda stats: stats.get("speed_demon_unlocked", False),
}


async def check_and_award(user_id: uuid.UUID, db: AsyncSession, extra: dict | None = None) -> list[dict]:
    """Check all achievement conditions and award any newly earned ones. Returns list of new achievements."""
    user = await db.get(User, user_id)
    if not user:
        return []

    # Gather stats
    docs_count = await db.scalar(
        select(func.count()).where(Document.user_id == user_id)
    )
    vocab_mastered = await db.scalar(
        select(func.count()).where(
            VocabularyItem.user_id == user_id,
        )
    )
    grammar_count = await db.scalar(
        select(func.count(GrammarPattern.id))
        .join(Document, GrammarPattern.document_id == Document.id)
        .where(Document.user_id == user_id)
    )

    stats = {
        "documents_uploaded": docs_count or 0,
        "exercises_completed": (extra or {}).get("exercises_done", 0),
        "streak_days": user.streak_days,
        "vocab_mastered": vocab_mastered or 0,
        "current_level": user.current_level,
        "grammar_patterns": grammar_count or 0,
        "speed_demon_unlocked": (extra or {}).get("speed_demon", False),
    }

    # Find already-earned achievement keys
    earned_rows = await db.execute(
        select(Achievement.key)
        .join(UserAchievement, Achievement.id == UserAchievement.achievement_id)
        .where(UserAchievement.user_id == user_id)
    )
    already_earned = {row[0] for row in earned_rows}

    new_achievements: list[dict] = []
    all_achievements = (await db.execute(select(Achievement))).scalars().all()

    for achievement in all_achievements:
        if achievement.key in already_earned:
            continue
        condition = ACHIEVEMENT_CONDITIONS.get(achievement.key)
        if condition and condition(stats):
            ua = UserAchievement(user_id=user_id, achievement_id=achievement.id)
            db.add(ua)
            user.total_xp += achievement.xp_reward
            new_achievements.append({
                "key": achievement.key,
                "name": achievement.name,
                "description": achievement.description,
                "icon": achievement.icon,
                "xp_reward": achievement.xp_reward,
            })

    if new_achievements:
        await db.flush()

    return new_achievements
