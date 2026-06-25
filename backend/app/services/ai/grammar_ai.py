import json
import logging
from app.services.ai.openai_client import get_client

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a German grammar expert. Analyze the following German sentences and identify \
grammar structures relevant to language learners.

For each pattern found, provide a JSON object with:
- pattern_type: one of [um_zu, modal_verb, separable_verb, subordinate_clause, dative_case,
  accusative_case, genitive_case, passive_voice, konjunktiv_ii, relative_clause,
  weil_clause, dass_clause, idiom, common_phrase]
- pattern_name: human-readable name (e.g. "Modal verb with infinitive")
- explanation: WHY this structure is used in this specific context (2-3 sentences, explain the \
communicative purpose, not just the rule)
- rule_summary: the grammar rule in one clear sentence
- example_from_doc: the exact sentence from the input that demonstrates this pattern
- example_translation: accurate English translation of that sentence
- difficulty: integer 1-5 (1=A1/A2 beginner, 5=C1/C2 advanced)

Return a JSON object with a single key "patterns" containing an array. \
If no significant patterns are found, return {"patterns": []}. \
Example: {"patterns": [{"pattern_type": "modal_verb", "pattern_name": "Modal verb with infinitive", ...}]}"""


async def detect_grammar_patterns(sentences: list[str]) -> list[dict]:
    """Send a batch of sentences to GPT-4o for grammar pattern detection and explanation."""
    if not sentences:
        return []

    sentences_text = "\n".join(f"- {s}" for s in sentences[:30])  # cap at 30 per batch

    client = get_client()
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Analyze these German sentences:\n\n{sentences_text}"},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        raw = response.choices[0].message.content or "{}"
        parsed = json.loads(raw)
        items = parsed.get("patterns", []) if isinstance(parsed, dict) else parsed
        if not isinstance(items, list):
            return []
        return items
    except Exception as exc:
        logger.error("grammar_ai failed: %s", exc)
        return []
