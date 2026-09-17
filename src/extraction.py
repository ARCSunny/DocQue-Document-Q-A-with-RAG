from __future__ import annotations

from .retrieval import HybridRetriever


def search_across_documents(query: str, retriever: HybridRetriever) -> dict:
    """Returns retrieval results grouped by source file for a multi-document
    search view using optimized hybrid retrieval."""
    chunks = retriever.retrieve(query=query, mode="hybrid", rerank=True)
    grouped: dict[str, list] = {}
    for c in chunks:
        grouped.setdefault(c.metadata["file_name"], []).append(
            {
                "page": c.metadata["page"],
                "unit_type": c.metadata["unit_type"],
                "text": c.text,
                "score": c.rerank_score or c.fused_score,
            }
        )
    return grouped