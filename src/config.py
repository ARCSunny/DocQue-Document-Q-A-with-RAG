import os
from dataclasses import dataclass, field
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
EXPORT_DIR = DATA_DIR / "exports"
CHROMA_DIR = BASE_DIR / "chroma_db"

for d in (UPLOAD_DIR, EXPORT_DIR, CHROMA_DIR):
    d.mkdir(parents=True, exist_ok=True)


@dataclass
class Settings:
    # --- LLM ---
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")

    # --- Ollama (local models, no API key needed) ---
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3.1")          
    ollama_vision_model: str = os.getenv("OLLAMA_VISION_MODEL", "llava")  

    # --- Embeddings ---
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
    embedding_dim: int = 384

    # --- Reranker ---
    reranker_model: str = os.getenv(
        "RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2"
    )
    rerank_top_n: int = 5             
    retrieval_top_k: int = 20       

    # --- Hybrid retrieval weighting ---
    vector_weight: float = 0.6
    bm25_weight: float = 0.4

    # --- Chunking ---
    chunk_size: int = 512
    chunk_overlap: int = 64
    table_chunk_size: int = 1024    

    # --- OCR ---
    ocr_lang: str = os.getenv("OCR_LANG", "eng")
    ocr_dpi: int = 300

    # --- Collections ---
    collection_name: str = "documents"

    # --- Conversation memory ---
    memory_turns: int = 6  


settings = Settings()