import json
import logging
import asyncio
from app.services.ai.openai_client import get_client

logger = logging.getLogger(__name__)

VOCAB_BATCH_PROMPT = """You are a German language exercise designer. For each word in the list below, \
generate exactly 3 exercises. Return a JSON object with key "results" containing an array of objects, \
one per word, each with keys "german_word" and "exercises" (array of 3 exercise objects).

Exercise types to generate per word:
1. fill_blank: blank out the target word in its example sentence with ___
   Keys: exercise_type="fill_blank", prompt, correct_answer, hint (plain English sentence e.g. "Starts with 'e' and is 6 letters long"), explanation
2. multiple_choice: "What does [word] mean?" with 4 options
   Keys: exercise_type="multiple_choice", prompt, correct_answer (English), distractors (3 wrong English options), explanation
3. translation_en_de: give the English sentence, ask for German translation
   Keys: exercise_type="translation_en_de", prompt (English sentence), correct_answer (German sentence), hint (a useful grammar or vocabulary tip for the translation), explanation

Example output format:
{"results": [{"german_word": "lernen", "exercises": [{...}, {...}, {...}]}, ...]}"""

GRAMMAR_BATCH_PROMPT = """You are a German grammar exercise designer. For each grammar pattern below, \
generate exactly 3 exercises. Return a JSON object with key "results" containing an array of objects, \
one per pattern, each with keys "pattern_type" and "exercises" (array of 3 exercise objects).

Exercise types to generate per pattern:
1. fill_blank: blank out the key structural element in the example sentence
   Keys: exercise_type="fill_blank", prompt, correct_answer, hint, explanation
2. sentence_builder: scrambled words from the example sentence
   Keys: exercise_type="sentence_builder", prompt="Arrange these words into a correct German sentence:", \
correct_answer (full sentence), distractors (array of scrambled words), explanation
3. translation_de_en: translate the example sentence German→English
   Keys: exercise_type="translation_de_en", prompt (German sentence), correct_answer (English), explanation

Example output format:
{"results": [{"pattern_type": "modal_verb", "exercises": [{...}, {...}, {...}]}, ...]}"""

BATCH_SIZE = 10  # words/patterns per GPT call


async def _call_gpt(system: str, user: str) -> dict:
    client = get_client()
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        response_format={"type": "json_object"},
        temperature=0.4,
    )
    raw = response.choices[0].message.content or "{}"
    return json.loads(raw)


async def generate_vocabulary_exercises_batch(vocab_items: list[dict]) -> dict[str, list[dict]]:
    """Generate exercises for a batch of vocabulary items in one GPT call.
    Returns dict mapping german_word → list of exercises."""
    if not vocab_items:
        return {}

    word_list = "\n".join(
        f"{i+1}. Word: {v['german_word']} | Translation: {v.get('translation_en','')} | "
        f"POS: {v.get('part_of_speech','')} | Example: {v.get('example_sentence','')[:100]} | "
        f"Difficulty: {v.get('difficulty',3)}/5"
        for i, v in enumerate(vocab_items)
    )
    try:
        parsed = await _call_gpt(VOCAB_BATCH_PROMPT, f"Generate exercises for these words:\n\n{word_list}")
        results = parsed.get("results", [])
        return {r["german_word"]: r.get("exercises", []) for r in results if isinstance(r, dict)}
    except Exception as exc:
        logger.error("vocab batch exercise generation failed: %s", exc)
        return {}


async def generate_grammar_exercises_batch(patterns: list[dict]) -> dict[str, list[dict]]:
    """Generate exercises for a batch of grammar patterns in one GPT call.
    Returns dict mapping pattern_type → list of exercises."""
    if not patterns:
        return {}

    pattern_list = "\n".join(
        f"{i+1}. Type: {p['pattern_type']} | Name: {p['pattern_name']} | "
        f"Rule: {p['rule_summary']} | Example: {p['example_from_doc'][:120]} | "
        f"Translation: {p['example_translation'][:100]}"
        for i, p in enumerate(patterns)
    )
    try:
        parsed = await _call_gpt(GRAMMAR_BATCH_PROMPT, f"Generate exercises for these patterns:\n\n{pattern_list}")
        results = parsed.get("results", [])
        # Key by index since pattern_types can repeat
        return {str(i): r.get("exercises", []) for i, r in enumerate(results) if isinstance(r, dict)}
    except Exception as exc:
        logger.error("grammar batch exercise generation failed: %s", exc)
        return {}


async def generate_all_vocab_exercises(vocab_items: list[dict]) -> list[list[dict]]:
    """Run batched exercise generation for all vocab items concurrently."""
    batches = [vocab_items[i:i + BATCH_SIZE] for i in range(0, len(vocab_items), BATCH_SIZE)]
    batch_results = await asyncio.gather(*[generate_vocabulary_exercises_batch(b) for b in batches])

    exercises_per_item: list[list[dict]] = []
    for item in vocab_items:
        word = item["german_word"]
        for batch_map in batch_results:
            if word in batch_map:
                exercises_per_item.append(batch_map[word])
                break
        else:
            exercises_per_item.append([])
    return exercises_per_item


async def generate_all_grammar_exercises(patterns: list[dict]) -> list[list[dict]]:
    """Run batched exercise generation for all grammar patterns concurrently."""
    batches = [patterns[i:i + BATCH_SIZE] for i in range(0, len(patterns), BATCH_SIZE)]
    batch_maps = await asyncio.gather(*[generate_grammar_exercises_batch(b) for b in batches])

    all_exercises: list[list[dict]] = []
    for batch, batch_map in zip(batches, batch_maps):
        for i in range(len(batch)):
            all_exercises.append(batch_map.get(str(i), []))
    return all_exercises
