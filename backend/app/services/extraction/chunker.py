import tiktoken

CHUNK_SIZE_TOKENS = 800
CHUNK_OVERLAP_TOKENS = 100

_enc = tiktoken.get_encoding("cl100k_base")


def _count_tokens(text: str) -> int:
    return len(_enc.encode(text))


def chunk_text(text: str, sentences: list[str]) -> list[str]:
    """
    Split text into overlapping chunks of ~CHUNK_SIZE_TOKENS tokens,
    respecting sentence boundaries.
    """
    chunks: list[str] = []
    current_chunk: list[str] = []
    current_tokens = 0

    for sentence in sentences:
        sentence_tokens = _count_tokens(sentence)
        if current_tokens + sentence_tokens > CHUNK_SIZE_TOKENS and current_chunk:
            chunks.append(" ".join(current_chunk))
            # Keep last N tokens worth of sentences for overlap
            overlap: list[str] = []
            overlap_tokens = 0
            for s in reversed(current_chunk):
                t = _count_tokens(s)
                if overlap_tokens + t <= CHUNK_OVERLAP_TOKENS:
                    overlap.insert(0, s)
                    overlap_tokens += t
                else:
                    break
            current_chunk = overlap
            current_tokens = overlap_tokens
        current_chunk.append(sentence)
        current_tokens += sentence_tokens

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks
