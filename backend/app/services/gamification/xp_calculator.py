XP_TABLE = {
    "flashcard": {"correct": 5, "incorrect": 1},
    "fill_blank": {"correct": 10, "incorrect": 2},
    "translation_de_en": {"correct": 15, "incorrect": 2},
    "translation_en_de": {"correct": 15, "incorrect": 2},
    "sentence_builder": {"correct": 12, "incorrect": 2},
    "multiple_choice": {"correct": 8, "incorrect": 1},
    "reading_comprehension": {"correct": 20, "incorrect": 2},
    "short_quiz": {"correct": 10, "incorrect": 1},
}
SESSION_COMPLETION_BONUS = 25


def xp_for_attempt(exercise_type: str, is_correct: bool) -> int:
    row = XP_TABLE.get(exercise_type, {"correct": 5, "incorrect": 1})
    return row["correct"] if is_correct else row["incorrect"]


def level_for_xp(total_xp: int) -> int:
    """Level 1=0 XP, Level 2=100 XP, each subsequent: level * 150 more."""
    level = 1
    threshold = 0
    while True:
        threshold += 100 if level == 1 else level * 150
        if total_xp < threshold:
            return level
        level += 1


def xp_to_next_level(total_xp: int) -> int:
    level = level_for_xp(total_xp)
    threshold = 100
    for l in range(2, level + 1):
        threshold += l * 150
    return threshold - total_xp
