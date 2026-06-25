from functools import lru_cache
from wordfreq import zipf_frequency

import spacy
from spacy.tokens import Doc

KEEP_POS = {"NOUN", "VERB", "ADJ", "ADV"}
# Words with Zipf frequency >= 5.0 are extremely common (e.g. "sein", "haben") — skip them
ZIPF_THRESHOLD = 4.5
# Minimum character length
MIN_WORD_LEN = 3


@lru_cache(maxsize=1)
def _load_model():
    return spacy.load("de_core_news_lg")


def analyze(text: str) -> Doc:
    nlp = _load_model()
    return nlp(text)


def extract_candidate_vocabulary(text: str) -> list[dict]:
    """
    Return a deduplicated list of vocabulary candidates from the text,
    filtering to content words below a Zipf frequency threshold.
    """
    doc = analyze(text)
    seen_lemmas: set[str] = set()
    candidates: list[dict] = []

    for token in doc:
        if token.pos_ not in KEEP_POS:
            continue
        if token.is_stop or token.is_punct or token.is_space:
            continue
        if len(token.text) < MIN_WORD_LEN:
            continue
        lemma = token.lemma_.lower()
        if lemma in seen_lemmas:
            continue
        freq = zipf_frequency(lemma, "de")
        if freq >= ZIPF_THRESHOLD:
            continue
        seen_lemmas.add(lemma)
        # Find the sentence containing this token
        sent_text = token.sent.text.strip()
        candidates.append({
            "german_word": token.text,
            "lemma": lemma,
            "pos": token.pos_,
            "example_sentence": sent_text,
        })

    return candidates


def extract_sentences_for_grammar(text: str) -> list[str]:
    """Return all sentences from the text for grammar pattern detection."""
    doc = analyze(text)
    return [sent.text.strip() for sent in doc.sents if len(sent.text.strip()) > 20]
