from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
from sentence_transformers import CrossEncoder

from .config import settings
from .indexing import IndexManager

logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    chunk_id: str
    text: str
    metadata: dict
    vector_score: float = 0.0
    bm25_score: float = 0.0
    fused_score: float = 0.0
    rerank_score: float = 0.0


class HybridRetriever:
    def __init__(self, index_manager: IndexManager):
        self.index_manager = index_manager
        self._reranker: CrossEncoder | None = None

    @property
    def reranker(self) -> CrossEncoder:
        if self._reranker is None:
            self._reranker = CrossEncoder(settings.reranker_model)
        return self._reranker

    # ------------------------------------------------------------------ #
    def _vector_search(self, query: str, top_k: int, doc_filter: list[str] | None):
        q_emb = self.index_manager.embed_query(query)
        where = {"file_name": {"$in": doc_filter}} if doc_filter else None
        res = self.index_manager.collection.query(
            query_embeddings=[q_emb], n_results=top_k, where=where,
        )
        out = []
        if res["ids"] and res["ids"][0]:
            for cid, doc, meta, dist in zip(
                res["ids"][0], res["documents"][0], res["metadatas"][0], res["distances"][0]
            ):
                similarity = 1 - dist  # cosine distance -> similarity
                out.append(RetrievedChunk(cid, doc, meta, vector_score=similarity))
        return out

    def _bm25_search(self, query: str, top_k: int, doc_filter: list[str] | None):
        bm25 = self.index_manager.bm25
        if bm25 is None:
            return []
        tokenized = query.lower().split()
        scores = bm25.get_scores(tokenized)
        ids = self.index_manager.bm25_corpus_ids
        ranked = np.argsort(scores)[::-1][:top_k]

        # Pull matching docs/metadata from Chroma by id for consistency.
        chunk_ids = [ids[i] for i in ranked if scores[i] > 0]
        if not chunk_ids:
            return []
        fetched = self.index_manager.collection.get(
            ids=chunk_ids, include=["documents", "metadatas"]
        )
        out = []
        for cid, doc, meta in zip(fetched["ids"], fetched["documents"], fetched["metadatas"]):
            if doc_filter and meta["file_name"] not in doc_filter:
                continue
            idx = ids.index(cid)
            out.append(RetrievedChunk(cid, doc, meta, bm25_score=float(scores[idx])))
        return out

    @staticmethod
    def _normalize(scores: list[float]) -> list[float]:
        if not scores:
            return []
        lo, hi = min(scores), max(scores)
        if hi - lo < 1e-9:
            return [1.0 for _ in scores]
        return [(s - lo) / (hi - lo) for s in scores]

    # ------------------------------------------------------------------ #
    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        top_n: int | None = None,
        doc_filter: list[str] | None = None,
        rerank: bool = True,
    ) -> list[RetrievedChunk]:
        top_k = top_k or settings.retrieval_top_k
        top_n = top_n or settings.rerank_top_n

        # Always runs optimized hybrid (vector + keyword) retrieval
        vector_hits = self._vector_search(query, top_k, doc_filter)
        bm25_hits = self._bm25_search(query, top_k, doc_filter)

        # ---- fuse ----
        merged: dict[str, RetrievedChunk] = {}
        v_norm = self._normalize([c.vector_score for c in vector_hits])
        for c, s in zip(vector_hits, v_norm):
            c.vector_score = s
            merged[c.chunk_id] = c

        b_norm = self._normalize([c.bm25_score for c in bm25_hits])
        for c, s in zip(bm25_hits, b_norm):
            c.bm25_score = s
            if c.chunk_id in merged:
                merged[c.chunk_id].bm25_score = s
            else:
                merged[c.chunk_id] = c

        for c in merged.values():
            c.fused_score = (
                settings.vector_weight * c.vector_score
                + settings.bm25_weight * c.bm25_score
            )

        candidates = sorted(merged.values(), key=lambda c: c.fused_score, reverse=True)[: top_k]

        if not candidates:
            return []

        if not rerank:
            return candidates[:top_n]

        # ---- cross-encoder rerank ----
        pairs = [(query, c.text) for c in candidates]
        rerank_scores = self.reranker.predict(pairs)
        for c, s in zip(candidates, rerank_scores):
            c.rerank_score = float(s)
        candidates.sort(key=lambda c: c.rerank_score, reverse=True)
        return candidates[:top_n]