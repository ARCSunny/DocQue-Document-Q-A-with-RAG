from __future__ import annotations

import logging
import pickle
from pathlib import Path

import chromadb
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

from .chunking import Chunk
from .config import CHROMA_DIR, settings

logger = logging.getLogger(__name__)

BM25_STORE_PATH = CHROMA_DIR / "bm25_store.pkl"


class IndexManager:
    def __init__(self):
        self.embedder = SentenceTransformer(settings.embedding_model)
        self.client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        self.collection = self.client.get_or_create_collection(
            name=settings.collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        self.bm25_corpus_ids: list[str] = []
        self.bm25_corpus_texts: list[list[str]] = []
        self.bm25: BM25Okapi | None = None
        self._load_bm25()

    # ---------------- persistence for BM25 (Chroma persists itself) -------- #
    def _load_bm25(self):
        if BM25_STORE_PATH.exists():
            with open(BM25_STORE_PATH, "rb") as f:
                data = pickle.load(f)
            self.bm25_corpus_ids = data["ids"]
            self.bm25_corpus_texts = data["texts"]
            if self.bm25_corpus_texts:
                self.bm25 = BM25Okapi(self.bm25_corpus_texts)

    def _save_bm25(self):
        with open(BM25_STORE_PATH, "wb") as f:
            pickle.dump(
                {"ids": self.bm25_corpus_ids, "texts": self.bm25_corpus_texts}, f
            )

    # ---------------------------- indexing ---------------------------- #
    def add_chunks(self, chunks: list[Chunk], batch_size: int = 64):
        if not chunks:
            return
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            embeddings = self.embedder.encode(
                [c.text for c in batch], show_progress_bar=False
            ).tolist()
            self.collection.add(
                ids=[c.chunk_id for c in batch],
                embeddings=embeddings,
                documents=[c.text for c in batch],
                metadatas=[c.metadata for c in batch],
            )
            for c in batch:
                self.bm25_corpus_ids.append(c.chunk_id)
                self.bm25_corpus_texts.append(c.text.lower().split())

        self.bm25 = BM25Okapi(self.bm25_corpus_texts)
        self._save_bm25()
        logger.info("Indexed %d chunks (vector + bm25)", len(chunks))

    def delete_document(self, doc_id: str):
        """Remove all chunks belonging to a given document from both indices."""
        self.collection.delete(where={"doc_id": doc_id})
        
        remaining = self.collection.get(include=["documents", "metadatas"])
        self.bm25_corpus_ids = remaining["ids"]
        self.bm25_corpus_texts = [d.lower().split() for d in remaining["documents"]]
        self.bm25 = BM25Okapi(self.bm25_corpus_texts) if self.bm25_corpus_texts else None
        self._save_bm25()

    def list_documents(self) -> list[str]:
        data = self.collection.get(include=["metadatas"])
        return sorted({m["file_name"] for m in data["metadatas"]}) if data["metadatas"] else []

    def embed_query(self, query: str):
        return self.embedder.encode([query]).tolist()[0]