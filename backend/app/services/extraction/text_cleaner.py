import re


def clean_srt(text: str) -> str:
    """Strip SRT subtitle timestamps and index numbers, keeping only dialogue."""
    # Remove SRT index numbers
    text = re.sub(r"^\d+\s*$", "", text, flags=re.MULTILINE)
    # Remove timestamp lines: 00:00:00,000 --> 00:00:00,000
    text = re.sub(r"\d{2}:\d{2}:\d{2}[,\.]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[,\.]\d{3}", "", text)
    # Remove HTML tags sometimes present in SRT
    text = re.sub(r"<[^>]+>", "", text)
    # Remove [Speaker Name:] labels
    text = re.sub(r"\[[^\]]+\]", "", text)
    # Collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def clean_youtube_transcript(text: str) -> str:
    """Strip YouTube auto-generated transcript timestamps like [00:00:00]."""
    text = re.sub(r"\[\d{1,2}:\d{2}(?::\d{2})?\]", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def clean_plain_text(text: str) -> str:
    """Normalize whitespace and remove non-printable characters."""
    text = re.sub(r"[^\S\n]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def detect_and_clean(raw_text: str, source_type: str) -> str:
    if source_type in ("transcript_movie",):
        return clean_srt(raw_text)
    elif source_type == "transcript_youtube":
        return clean_youtube_transcript(raw_text)
    else:
        return clean_plain_text(raw_text)
