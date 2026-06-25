import json
import logging
from app.services.ai.openai_client import get_client

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a German language learning assistant. You will be given a list of German words \
extracted from an authentic document. For each word, provide:
1. The base lemma form
2. English translation (context-appropriate, not just dictionary definition)
3. Part of speech (noun/verb/adjective/adverb/phrase)
4. For nouns: the grammatical gender (der/die/das) and common plural form (null if not applicable)
5. CEFR difficulty level (A1/A2/B1/B2/C1/C2)
6. difficulty as integer 1-5 (1=A1/A2, 3=B1/B2, 5=C1/C2)

Return ONLY a JSON array of objects with keys: \
german_word, lemma, translation_en, part_of_speech, gender, plural_form, cefr_level, difficulty.
No explanations outside the JSON."""


async def enrich_vocabulary(candidates: list[dict], context_chunk: str) -> list[dict]:
    """Call GPT-4o to enrich a batch of vocabulary candidates with translations and metadata."""
    if not candidates:
        return []

    word_list = "\n".join(
        f"{i+1}. {c['german_word']} (example: {c['example_sentence'][:80]})"
        for i, c in enumerate(candidates)
    )
    user_message = f"Document context (first 400 chars):\n{context_chunk[:400]}\n\nWords to enrich:\n{word_list}"

    client = get_client()
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        raw = response.choices[0].message.content or "{}"
        # GPT-4o with json_object wraps arrays in an object
        parsed = json.loads(raw)
        items = parsed if isinstance(parsed, list) else next(iter(parsed.values()), [])
        return items
    except Exception as exc:
        logger.error("vocabulary_ai failed: %s", exc)
        return []
