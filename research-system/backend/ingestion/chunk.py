from dataclasses import dataclass

CHUNK_SIZE = 512
CHUNK_OVERLAP = 64


@dataclass
class Chunk:
    index: int
    text: str


def chunk_text(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[Chunk]:
    """Split text into overlapping word-based chunks."""
    words = text.split()
    if not words:
        return []
    chunks: list[Chunk] = []
    step = chunk_size - overlap
    chunk_index = 0
    for start in range(0, len(words), step):
        chunk_words = words[start : start + chunk_size]
        if not chunk_words:
            break
        chunks.append(Chunk(index=chunk_index, text=" ".join(chunk_words)))
        chunk_index += 1
    return chunks
