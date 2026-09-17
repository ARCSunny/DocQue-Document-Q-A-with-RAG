from __future__ import annotations

import uuid
from dataclasses import dataclass, field

import tiktoken

from .config import settings
from .ingestion import RawUnit

_enc = tiktoken.get_encoding("cl100k_base")


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    file_name: str
    page: int
    unit_type: str
    text: str
    metadata: dict = field(default_factory=dict)


def _split_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    tokens = _enc.encode(text)
    if len(tokens) <= chunk_size:
        return [text]
    chunks = []
    start = 0
    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunks.append(_enc.decode(tokens[start:end]))
        if end == len(tokens):
            break
        start = end - overlap
    return chunks


def chunk_units(units: list[RawUnit]) -> list[Chunk]:
    chunks: list[Chunk] = []
    for u in units:
        if u.unit_type in ("text", "ocr_text"):
            pieces = _split_text(u.content, settings.chunk_size, settings.chunk_overlap)
        elif u.unit_type == "table":
            pieces = _split_text(u.content, settings.table_chunk_size, 0)
        else:  # image_caption — keep whole
            pieces = [u.content]

        for i, piece in enumerate(pieces):
            chunks.append(
                Chunk(
                    chunk_id=str(uuid.uuid4()),
                    doc_id=u.doc_id,
                    file_name=u.file_name,
                    page=u.page,
                    unit_type=u.unit_type,
                    text=piece,
                    metadata={
                        "doc_id": u.doc_id,
                        "file_name": u.file_name,
                        "page": u.page,
                        "unit_type": u.unit_type,
                        "chunk_part": i,
                        **({"table_index": u.extra["table_index"]}
                           if "table_index" in u.extra else {}),
                    },
                )
            )
    return chunks
