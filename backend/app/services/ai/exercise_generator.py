import json
import logging
from app.services.ai.openai_client import get_client

logger = logging.getLogger(__name__)

VOCAB_EXERCISE_PROMPT = """You are a German language exercise designer. Given the German word and context below, \
generate exactly 3 exercises as a JSON array:

1. fill_blank: Take the example sentence and blank out the target word with ___.
   Include: exercise_type="fill_blank", prompt (the sentence with blank), correct_answer (the word), \
   hint (first letter + length), explanation (why this word fits).

2. multiple_choice: Ask "What does '{word}' mean?".
   Include: exercise_type="multiple_choice", prompt, correct_answer (English translation), \
   distractors (array of 3 plausible wrong English translations), explanation.

3. translation_en_de: Give the English sentence and ask the user to translate it to German.
   Include: exercise_type="translation_en_de", prompt (English sentence), correct_answer (German sentence), \
   hint, explanation.

Return ONLY a JSON array of exactly 3 exercise objects."""

GRAMMAR_EXERCISE_PROMPT = """You are a German grammar exercise designer. Given the grammar pattern and example below, \
generate exactly 3 exercises as a JSON array:

1. fill_blank: Blank out the key structural element in the example sentence.
   Include: exercise_type="fill_blank", prompt, correct_answer, hint, explanation.

2. sentence_builder: Provide the words of the example sentence in scrambled order.
   Include: exercise_type="sentence_builder", prompt="Arrange these words into a correct German sentence:", \
   correct_answer (the full sentence), distractors (array of the scrambled words), explanation (what makes \
   this structure correct).

3. translation_de_en: Ask the user to translate the example sentence from German to English.
   Include: exercise_type="translation_de_en", prompt (the German sentence), correct_answer (English), \
   explanation (focusing on the grammar structure).

Return ONLY a JSON array of exactly 3 exercise objects."""


async def generate_vocabulary_exercises(vocab_item: dict) -> list[dict]:
    client = get_client()
    user_msg = (
        f"Word: {vocab_item['german_word']}\n"
        f"Translation: {vocab_item['translation_en']}\n"
        f"Part of speech: {vocab_item.get('part_of_speech', '')}\n"
        f"Example sentence: {vocab_item.get('example_sentence', '')}\n"
        f"Difficulty: {vocab_item.get('difficulty', 3)}/5"
    )
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": VOCAB_EXERCISE_PROMPT.replace("{word}", vocab_item["german_word"])},
                {"role": "user", "content": user_msg},
            ],
            response_format={"type": "json_object"},
            temperature=0.4,
        )
        raw = response.choices[0].message.content or "[]"
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, list) else next(iter(parsed.values()), [])
    except Exception as exc:
        logger.error("vocab exercise generation failed: %s", exc)
        return []


async def generate_grammar_exercises(pattern: dict) -> list[dict]:
    client = get_client()
    user_msg = (
        f"Pattern: {pattern['pattern_name']}\n"
        f"Rule: {pattern['rule_summary']}\n"
        f"Example: {pattern['example_from_doc']}\n"
        f"Translation: {pattern['example_translation']}\n"
        f"Difficulty: {pattern.get('difficulty', 3)}/5"
    )
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": GRAMMAR_EXERCISE_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            response_format={"type": "json_object"},
            temperature=0.4,
        )
        raw = response.choices[0].message.content or "[]"
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, list) else next(iter(parsed.values()), [])
    except Exception as exc:
        logger.error("grammar exercise generation failed: %s", exc)
        return []
