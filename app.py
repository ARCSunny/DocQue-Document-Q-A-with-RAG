from __future__ import annotations

import uuid
from pathlib import Path

import streamlit as st

from src.chunking import chunk_units
from src.config import UPLOAD_DIR, settings
from src.extraction import (
    search_across_documents,
)
from src.generation import generate_answer
from src.indexing import IndexManager
from src.ingestion import ingest_file
from src.llm_client import describe_image
from src.memory import ConversationMemory
from src.retrieval import HybridRetriever

st.set_page_config(page_title="DocQue", layout="wide")


# --------------------------------------------------------------------------- #
# Cached singletons
# --------------------------------------------------------------------------- #
@st.cache_resource
def get_index_manager() -> IndexManager:
    return IndexManager()


@st.cache_resource
def get_retriever(_index_manager: IndexManager) -> HybridRetriever:
    return HybridRetriever(_index_manager)


if "memory" not in st.session_state:
    st.session_state.memory = ConversationMemory()
if "chat_log" not in st.session_state:
    st.session_state.chat_log = []  

index_manager = get_index_manager()
retriever = get_retriever(index_manager)

# App Header
st.title("📚 DocQue")
st.caption("A lightweight, streamlined RAG application for chatting with and querying your documents efficiently.")

# Main navigation tabs
tabs = st.tabs(["📤 Upload & Index", "💬 Chat", "🔎 Search"])

# --------------------------------------------------------------------------- #
# TAB 1: Upload & Index
# --------------------------------------------------------------------------- #
with tabs[0]:
    st.subheader("Upload documents")
    st.write("Supports PDF (native, scanned/OCR, tables, embedded images/charts) and DOCX.")
    
    uploaded = st.file_uploader(
        "Choose PDF or DOCX files", type=["pdf", "docx"], accept_multiple_files=True
    )

    if uploaded and st.button("Ingest & Index"):
        progress = st.progress(0.0, text="Starting...")
        for i, uf in enumerate(uploaded):
            dest = UPLOAD_DIR / uf.name
            dest.write_bytes(uf.getbuffer())
            doc_id = str(uuid.uuid4())

            progress.progress((i + 0.3) / len(uploaded), text=f"Parsing {uf.name}...")
            # Automatically process images, charts, and receipts using vision LLM
            units = ingest_file(str(dest), doc_id, describe_images_fn=describe_image)

            progress.progress((i + 0.6) / len(uploaded), text=f"Chunking {uf.name}...")
            chunks = chunk_units(units)

            progress.progress((i + 0.8) / len(uploaded), text=f"Embedding & indexing {uf.name}...")
            index_manager.add_chunks(chunks)

            progress.progress((i + 1) / len(uploaded), text=f"Done: {uf.name}")
            st.success(f"Indexed {uf.name}: {len(units)} units -> {len(chunks)} chunks")
        st.rerun()

    st.divider()
    st.subheader("Indexed documents")
    docs = index_manager.list_documents()
    if docs:
        for d in docs:
            col1, col2 = st.columns([4, 1])
            col1.write(f"📄 {d}")
            if col2.button("Delete", key=f"del_{d}"):
                index_manager.delete_document_by_name = getattr(
                    index_manager, "delete_document_by_name", None
                )
                index_manager.collection.delete(where={"file_name": d})
                st.rerun()
    else:
        st.info("No documents indexed yet. Upload above.")

# --------------------------------------------------------------------------- #
# TAB 2: Chat
# --------------------------------------------------------------------------- #
with tabs[1]:
    st.subheader("Ask questions about your documents")

    all_docs = index_manager.list_documents()
    doc_filter_choice = []
    
    if all_docs:
        with st.expander("⚙️ Filter by specific documents (Optional)", expanded=False):
            if "select_all_docs" not in st.session_state:
                st.session_state.select_all_docs = True
                for d in all_docs:
                    st.session_state[f"doc_{d}"] = True

            def toggle_select_all():
                val = st.session_state.select_all_toggle
                for d in all_docs:
                    st.session_state[f"doc_{d}"] = val

            st.checkbox(
                "Select all", 
                key="select_all_toggle", 
                value=st.session_state.select_all_docs, 
                on_change=toggle_select_all
            )
            
            for d in all_docs:
                if st.checkbox(d, key=f"doc_{d}"):
                    doc_filter_choice.append(d)

    if st.button("🗑️ Clear conversation"):
        st.session_state.memory.clear()
        st.session_state.chat_log = []
        st.rerun()

    for turn in st.session_state.chat_log:
        with st.chat_message(turn["role"]):
            st.markdown(turn["content"])
            if turn.get("citations"):
                with st.expander("Sources"):
                    for c in turn["citations"]:
                        st.markdown(f"**[{c.index}]** {c.file_name}, page {c.page} ({c.unit_type})")
                        st.caption(c.snippet)

    question = st.chat_input("Ask a question about your documents...")
    if question:
        st.session_state.chat_log.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            try:
                with st.spinner("Analyzing documents to find the best answer..."):
                    # Automatically uses the optimized hybrid retrieval method under the hood
                    chunks = retriever.retrieve(
                        question,
                        doc_filter=doc_filter_choice or None,
                    )

                with st.spinner("Generating answer..."):
                    answer = generate_answer(question, chunks, st.session_state.memory.as_list())

                st.markdown(answer.text)
                if answer.citations:
                    with st.expander("Sources"):
                        for c in answer.citations:
                            st.markdown(f"**[{c.index}]** {c.file_name}, page {c.page} ({c.unit_type})")
                            st.caption(c.snippet)

                st.session_state.memory.add("user", question)
                st.session_state.memory.add("assistant", answer.text)
                st.session_state.chat_log.append(
                    {"role": "assistant", "content": answer.text, "citations": answer.citations}
                )
            except Exception as e:
                if "429" in str(e) or "ResourceExhausted" in str(e):
                    st.error("⚠️ **API Quota Exceeded:** You have hit the Google AI Studio free tier limit (20 requests/day). Please wait a short while or link a billing account in Google AI Studio to lift this restriction.")
                else:
                    raise e

# --------------------------------------------------------------------------- #
# TAB 3: Cross-document search
# --------------------------------------------------------------------------- #
with tabs[2]:
    st.subheader("Search across all documents")
    st.caption("Quickly find specific phrases, data points, or concepts across your entire document library.")
    
    q = st.text_input("Search query", placeholder="Type a keyword or phrase...")

    if q:
        with st.spinner("Searching across documents..."):
            grouped = search_across_documents(q, retriever)
            
        if not grouped:
            st.info("No matching results found in your documents.")
        else:
            total_hits = sum(len(hits) for hits in grouped.values())
            st.success(f"Found **{total_hits}** matching sections across **{len(grouped)}** documents.")
            st.divider()
            
            for fname, hits in grouped.items():
                st.markdown(f"### 📄 {fname}")
                for h in hits:
                    with st.container(border=True):
                        col1, col2 = st.columns([5, 1])
                        col1.write(f"**Page {h['page']}** ({h['unit_type']})")
                        col2.caption(f"Score: {h['score']:.2f}")
                        st.markdown(f"> {h['text'][:400]}...")