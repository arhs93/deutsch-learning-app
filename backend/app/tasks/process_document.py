import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Document, VocabularyItem, GrammarPattern, Exercise, Flashcard
from app.services.extraction.pdf_extractor import extract_text_from_pdf
from app.services.extraction.text_cleaner import detect_and_clean
from app.services.extraction.chunker import chunk_text
from app.services.nlp.spacy_analyzer import (
    analyze,
    extract_candidate_vocabulary,
    extract_sentences_for_grammar,
)
from app.services.ai.vocabulary_ai import enrich_vocabulary
from app.services.ai.grammar_ai import detect_grammar_patterns
from app.services.ai.exercise_generator import generate_vocabulary_exercises, generate_grammar_exercises

logger = logging.getLogger(__name__)

BATCH_SIZE = 20  # vocabulary items per GPT-4o call


async def process_document(document_id: uuid.UUID, db: AsyncSession) -> None:
    doc = await db.get(Document, document_id)
    if not doc:
        logger.error("Document %s not found", document_id)
        return

    try:
        doc.processing_status = "processing"
        await db.commit()

        # 1. Extract text
        file_path = Path(doc.storage_path)
        if doc.source_type == "pdf":
            raw_text = extract_text_from_pdf(file_path)
        else:
            raw_text = file_path.read_text(encoding="utf-8", errors="replace")

        cleaned_text = detect_and_clean(raw_text, doc.source_type)
        doc.raw_text = cleaned_text
        doc.word_count = len(cleaned_text.split())
        await db.commit()

        # 2. Chunk with spaCy sentence boundaries
        spacy_doc = analyze(cleaned_text)
        sentences = [s.text.strip() for s in spacy_doc.sents if s.text.strip()]
        chunks = chunk_text(cleaned_text, sentences)

        # 3. Vocabulary extraction (batched)
        all_candidates: list[dict] = []
        seen_lemmas: set[str] = set()
        for chunk in chunks:
            candidates = extract_candidate_vocabulary(chunk)
            for c in candidates:
                if c["lemma"] not in seen_lemmas:
                    seen_lemmas.add(c["lemma"])
                    all_candidates.append(c)

        enriched_vocab: list[dict] = []
        for i in range(0, len(all_candidates), BATCH_SIZE):
            batch = all_candidates[i : i + BATCH_SIZE]
            context_chunk = chunks[min(i // BATCH_SIZE, len(chunks) - 1)]
            enriched = await enrich_vocabulary(batch, context_chunk)
            for item, raw in zip(batch, enriched):
                merged = {**item, **raw}
                enriched_vocab.append(merged)

        # 4. Save vocabulary items and create flashcards
        vocab_db_items: list[VocabularyItem] = []
        for v in enriched_vocab:
            vi = VocabularyItem(
                document_id=doc.id,
                user_id=doc.user_id,
                german_word=v.get("german_word", ""),
                lemma=v.get("lemma"),
                translation_en=v.get("translation_en", ""),
                part_of_speech=v.get("part_of_speech"),
                gender=v.get("gender"),
                plural_form=v.get("plural_form"),
                difficulty=v.get("difficulty"),
                example_sentence=v.get("example_sentence"),
                cefr_level=v.get("cefr_level"),
            )
            db.add(vi)
            vocab_db_items.append(vi)

        await db.flush()

        # Create flashcards for each vocabulary item
        for vi in vocab_db_items:
            flashcard = Flashcard(user_id=doc.user_id, vocabulary_item_id=vi.id)
            db.add(flashcard)

        # 5. Grammar detection (all sentences, batched)
        all_sentences = extract_sentences_for_grammar(cleaned_text)
        grammar_results: list[dict] = []
        seen_patterns: set[str] = set()
        for i in range(0, len(all_sentences), 30):
            batch = all_sentences[i : i + 30]
            patterns = await detect_grammar_patterns(batch)
            for p in patterns:
                key = p.get("pattern_type", "") + "|" + p.get("example_from_doc", "")[:50]
                if key not in seen_patterns:
                    seen_patterns.add(key)
                    grammar_results.append(p)

        # 6. Save grammar patterns
        grammar_db_items: list[GrammarPattern] = []
        for g in grammar_results:
            gp = GrammarPattern(
                document_id=doc.id,
                pattern_type=g.get("pattern_type", "unknown"),
                pattern_name=g.get("pattern_name", ""),
                explanation=g.get("explanation", ""),
                rule_summary=g.get("rule_summary", ""),
                example_from_doc=g.get("example_from_doc", ""),
                example_translation=g.get("example_translation", ""),
                difficulty=g.get("difficulty"),
                ai_analysis=g,
            )
            db.add(gp)
            grammar_db_items.append(gp)

        await db.flush()

        # 7. Generate exercises for vocabulary items
        for vi, v_dict in zip(vocab_db_items, enriched_vocab):
            exercises = await generate_vocabulary_exercises(v_dict)
            for ex_data in exercises:
                ex = Exercise(
                    document_id=doc.id,
                    vocabulary_item_id=vi.id,
                    exercise_type=ex_data.get("exercise_type", "fill_blank"),
                    prompt=ex_data.get("prompt", ""),
                    correct_answer=ex_data.get("correct_answer", ""),
                    distractors=ex_data.get("distractors"),
                    hint=ex_data.get("hint"),
                    explanation=ex_data.get("explanation"),
                    difficulty=v_dict.get("difficulty"),
                )
                db.add(ex)

        # 8. Generate exercises for grammar patterns
        for gp, g_dict in zip(grammar_db_items, grammar_results):
            exercises = await generate_grammar_exercises(g_dict)
            for ex_data in exercises:
                ex = Exercise(
                    document_id=doc.id,
                    grammar_pattern_id=gp.id,
                    exercise_type=ex_data.get("exercise_type", "fill_blank"),
                    prompt=ex_data.get("prompt", ""),
                    correct_answer=ex_data.get("correct_answer", ""),
                    distractors=ex_data.get("distractors"),
                    hint=ex_data.get("hint"),
                    explanation=ex_data.get("explanation"),
                    difficulty=g_dict.get("difficulty"),
                )
                db.add(ex)

        doc.processing_status = "ready"
        doc.processed_at = datetime.now(timezone.utc)
        await db.commit()
        logger.info("Document %s processed successfully", document_id)

    except Exception as exc:
        logger.exception("Failed to process document %s: %s", document_id, exc)
        doc.processing_status = "failed"
        await db.commit()
