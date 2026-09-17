from __future__ import annotations

from dataclasses import dataclass

from .llm_client import complete
from .retrieval import RetrievedChunk

SYSTEM_PROMPT = """You are a careful document Q&A assistant. Rules:
- Answer ONLY using the provided context excerpts. Do not use outside knowledge.
- Every factual claim must include a citation like [1], [2] referring to the
  excerpt number it came from.
- If the context does not contain the answer, say clearly that the documents
  do not contain enough information — do not guess or fabricate.
- Be concise and directly answer the question first, then add detail.
"""

ANSWER_PROMPT = """Conversation so far:
{history}

Context excerpts:
{context}

Question: {question}

Write the answer following the system rules, citing excerpt numbers in brackets.
"""


@dataclass
class Citation:
    index: int
    file_name: str
    page: int
    unit_type: str
    snippet: str


@dataclass
class Answer:
    text: str
    citations: list[Citation]
    used_chunks: list[RetrievedChunk]


def _format_context(chunks: list[RetrievedChunk]) -> tuple[str, list[Citation]]:
    lines = []
    citations = []
    for i, c in enumerate(chunks, start=1):
        lines.append(
            f"[{i}] (source: {c.metadata['file_name']}, page {c.metadata['page']}, "
            f"type: {c.metadata['unit_type']})\n{c.text}"
        )
        citations.append(
            Citation(
                index=i,
                file_name=c.metadata["file_name"],
                page=c.metadata["page"],
                unit_type=c.metadata["unit_type"],
                snippet=c.text[:300],
            )
        )
    return "\n\n".join(lines), citations


def generate_answer(question: str, chunks: list[RetrievedChunk], history: list[dict]) -> Answer:
    if not chunks:
        return Answer(
            text="I couldn't find relevant information in the uploaded documents to answer this question.",
            citations=[],
            used_chunks=[],
        )

    context, citations = _format_context(chunks)
    hist_str = "\n".join(f"{h['role']}: {h['content']}" for h in history[-6:]) or "(none)"
    prompt = ANSWER_PROMPT.format(history=hist_str, context=context, question=question)

    text = complete(prompt, system=SYSTEM_PROMPT, max_tokens=1024, temperature=0.1)
    return Answer(text=text, citations=citations, used_chunks=chunks)
