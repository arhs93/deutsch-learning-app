import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import Achievement, UserAchievement

router = APIRouter(tags=["achievements"])

SEED_DATA = [
    {"key": "first_document", "name": "First Upload", "description": "Upload your first document.", "icon": "📄", "xp_reward": 50, "condition_type": "documents_uploaded", "condition_value": 1},
    {"key": "first_exercise", "name": "First Step", "description": "Complete your first exercise.", "icon": "✏️", "xp_reward": 20, "condition_type": "exercises_completed", "condition_value": 1},
    {"key": "streak_3", "name": "3-Day Streak", "description": "Practice 3 days in a row.", "icon": "🔥", "xp_reward": 30, "condition_type": "streak", "condition_value": 3},
    {"key": "streak_7", "name": "Week Warrior", "description": "Practice 7 days in a row.", "icon": "🔥", "xp_reward": 70, "condition_type": "streak", "condition_value": 7},
    {"key": "streak_30", "name": "Monthly Master", "description": "Practice 30 days in a row.", "icon": "🏆", "xp_reward": 300, "condition_type": "streak", "condition_value": 30},
    {"key": "vocab_50", "name": "Word Collector", "description": "Learn 50 vocabulary items.", "icon": "📚", "xp_reward": 100, "condition_type": "vocab_count", "condition_value": 50},
    {"key": "vocab_100", "name": "Vocabulary Victor", "description": "Learn 100 vocabulary items.", "icon": "🎓", "xp_reward": 200, "condition_type": "vocab_count", "condition_value": 100},
    {"key": "level_5", "name": "Level 5 Reached", "description": "Reach level 5.", "icon": "⭐", "xp_reward": 150, "condition_type": "level", "condition_value": 5},
    {"key": "grammar_hunter", "name": "Grammar Hunter", "description": "Discover 10 grammar patterns.", "icon": "🔍", "xp_reward": 100, "condition_type": "grammar_patterns", "condition_value": 10},
    {"key": "polyglot", "name": "Polyglot", "description": "Upload 5 different documents.", "icon": "🌍", "xp_reward": 150, "condition_type": "documents_uploaded", "condition_value": 5},
    {"key": "speed_demon", "name": "Speed Demon", "description": "Complete 10 exercises in under 5 minutes.", "icon": "⚡", "xp_reward": 100, "condition_type": "speed", "condition_value": 10},
]


@router.post("/achievements/seed")
async def seed_achievements(db: AsyncSession = Depends(get_db)):
    """One-time seed endpoint to populate achievements table."""
    for data in SEED_DATA:
        existing = await db.scalar(select(Achievement).where(Achievement.key == data["key"]))
        if not existing:
            db.add(Achievement(**data))
    await db.commit()
    return {"seeded": len(SEED_DATA)}


@router.get("/achievements")
async def get_achievements(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    all_achievements = (await db.execute(select(Achievement))).scalars().all()
    earned_rows = await db.execute(
        select(UserAchievement).where(UserAchievement.user_id == user_id)
    )
    earned_map = {ua.achievement_id: ua.earned_at for ua in earned_rows.scalars().all()}

    return [
        {
            "key": a.key,
            "name": a.name,
            "description": a.description,
            "icon": a.icon,
            "xp_reward": a.xp_reward,
            "earned": a.id in earned_map,
            "earned_at": earned_map[a.id].isoformat() if a.id in earned_map else None,
        }
        for a in all_achievements
    ]
