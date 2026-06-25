import asyncio
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Document, VocabularyItem, GrammarPattern, Exercise, Flashcard
from app.services.extraction.pdf_extractor import extract_text_from_pdf
from app.services.extraction.text_cleaner import detect_and_clean
from app.services.extraction.chunker import chunk_text
from app.services.nlp.spacy_analyzer import analyze, extract_candidate_vocabulary, extract_sentences_for_grammar
from app.services.ai.vocabulary_ai import enrich_vocabulary
from app.services.ai.grammar_ai import detect_grammar_patterns
from app.services.ai.exercise_generator import generate_all_vocab_exercises, generate_all_grammar_exercises

logger = logging.getLogger(__name__)

VOCAB_BATCH = 20   # words per GPT-4o enrichment call
GRAMMAR_BATCH = 30 # sentences per GPT-4o grammar call


async def _enrich_all_vocabulary(candidates: list[dict], chunks: list[str]) -> list[dict]:
    """Enrich all vocabulary batches concurrently."""
    batches = [candidates[i:i + VOCAB_BATCH] for i in range(0, len(candidates), VOCAB_BATCH)]
    context_chunks = [chunks[min(i, len(chunks) - 1)] for i in range(len(batches))]

    results = await asyncio.gather(
        *[enrich_vocabulary(batch, ctx) for batch, ctx in zip(batches, context_chunks)],
        return_exceptions=True,
    )

    enriched: list[dict] = []
    for batch, result in zip(batches, results):
        if isinstance(result, Exception):
            logger.error("Vocabulary enrichment batch failed: %s", result)
            enriched.extend(batch)  # keep raw candidates as fallback
        else:
            for candidate, enriched_item in zip(batch, result):
                enriched.append({**candidate, **enriched_item} if isinstance(enriched_item, dict) else candidate)
    return enriched


async def _detect_all_grammar(sentences: list[str]) -> list[dict]:
    """Detect grammar patterns across all sentence batches concurrently."""
    batches = [sentences[i:i + GRAMMAR_BATCH] for i in range(0, len(sentences), GRAMMAR_BATCH)]

    results = await asyncio.gather(
        *[detect_grammar_patterns(batch) for batch in batches],
        return_exceptions=True,
    )

    seen_keys: set[str] = set()
    patterns: list[dict] = []
    for result in results:
        if isinstance(result, Exception):
            logger.error("Grammar detection batch failed: %s", result)
            continue
        for p in result:
            key = p.get("pattern_type", "") + "|" + p.get("example_from_doc", "")[:50]
            if key not in seen_keys:
                seen_keys.add(key)
                patterns.append(p)
    return patterns


async def process_document(document_id: uuid.UUID, db: AsyncSession) -> None:
    doc = await db.get(Document, document_id)
    if not doc:
        logger.error("Document %s not found", document_id)
        return

    try:
        doc.processing_status = "processing"
        await db.commit()

        # 1. Extract and clean text
        file_path = Path(doc.storage_path)
        raw_text = (
            extract_text_from_pdf(file_path)
            if doc.source_type == "pdf"
            else file_path.read_text(encoding="utf-8", errors="replace")
        )
        cleaned_text = detect_and_clean(raw_text, doc.source_type)
        doc.raw_text = cleaned_text
        doc.word_count = len(cleaned_text.split())
        await db.commit()

        # 2. spaCy: sentence segmentation + chunking + candidate extraction
        spacy_doc = analyze(cleaned_text)
        sentences = [s.text.strip() for s in spacy_doc.sents if s.text.strip()]
        chunks = chunk_text(cleaned_text, sentences)

        seen_lemmas: set[str] = set()
        all_candidates: list[dict] = []
        for chunk in chunks:
            for c in extract_candidate_vocabulary(chunk):
                if c["lemma"] not in seen_lemmas:
                    seen_lemmas.add(c["lemma"])
                    all_candidates.append(c)

        all_sentences = extract_sentences_for_grammar(cleaned_text)

        # 3. Run vocabulary enrichment and grammar detection IN PARALLEL
        logger.info("Document %s: %d vocab candidates, %d sentences — running AI in parallel",
                    document_id, len(all_candidates), len(all_sentences))

        enriched_vocab, grammar_results = await asyncio.gather(
            _enrich_all_vocabulary(all_candidates, chunks),
            _detect_all_grammar(all_sentences),
        )

        logger.info("Document %s: %d vocab enriched, %d grammar patterns found",
                    document_id, len(enriched_vocab), len(grammar_results))

        # 4. Save vocabulary items + flashcards
        vocab_db_items: list[VocabularyItem] = []
        for v in enriched_vocab:
            if not v.get("german_word") or not v.get("translation_en"):
                continue
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

        for vi in vocab_db_items:
            db.add(Flashcard(user_id=doc.user_id, vocabulary_item_id=vi.id))

        # 5. Save grammar patterns
        grammar_db_items: list[GrammarPattern] = []
        for g in grammar_results:
            if not g.get("pattern_name") or not g.get("example_from_doc"):
                continue
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

        # 6. Generate exercises for vocab + grammar IN PARALLEL
        logger.info("Document %s: generating exercises for %d vocab + %d grammar patterns",
                    document_id, len(vocab_db_items), len(grammar_db_items))

        vocab_exercises_list, grammar_exercises_list = await asyncio.gather(
            generate_all_vocab_exercises(enriched_vocab[:len(vocab_db_items)]),
            generate_all_grammar_exercises(grammar_results[:len(grammar_db_items)]),
        )

        # 7. Save vocab exercises
        for vi, exercises in zip(vocab_db_items, vocab_exercises_list):
            for ex_data in exercises:
                if not ex_data.get("prompt") or not ex_data.get("correct_answer"):
                    continue
                db.add(Exercise(
                    document_id=doc.id,
                    vocabulary_item_id=vi.id,
                    exercise_type=ex_data.get("exercise_type", "fill_blank"),
                    prompt=ex_data["prompt"],
                    correct_answer=ex_data["correct_answer"],
                    distractors=ex_data.get("distractors"),
                    hint=ex_data.get("hint"),
                    explanation=ex_data.get("explanation"),
                    difficulty=vi.difficulty,
                ))

        # 8. Save grammar exercises
        for gp, exercises in zip(grammar_db_items, grammar_exercises_list):
            for ex_data in exercises:
                if not ex_data.get("prompt") or not ex_data.get("correct_answer"):
                    continue
                db.add(Exercise(
                    document_id=doc.id,
                    grammar_pattern_id=gp.id,
                    exercise_type=ex_data.get("exercise_type", "fill_blank"),
                    prompt=ex_data["prompt"],
                    correct_answer=ex_data["correct_answer"],
                    distractors=ex_data.get("distractors"),
                    hint=ex_data.get("hint"),
                    explanation=ex_data.get("explanation"),
                    difficulty=gp.difficulty,
                ))

        doc.processing_status = "ready"
        doc.processed_at = datetime.now(timezone.utc)
        await db.commit()
        logger.info("Document %s processed successfully", document_id)

    except Exception as exc:
        logger.exception("Failed to process document %s: %s", document_id, exc)
        try:
            doc.processing_status = "failed"
            await db.commit()
        except Exception:
            pass
