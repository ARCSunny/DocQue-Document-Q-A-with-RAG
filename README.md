# DocQue-Document-Q-A-with-RAG
DocQue is a Streamlit-powered RAG application that lets you chat with and search complex documents (PDF/DOCX). It intelligently extracts, indexes, and retrieves precise excerpts—supporting text, scans, tables, and charts—to generate accurate, context-grounded answers with instant source citations.

## ✨ Features

### 📤 Document Upload & Indexing

- Upload multiple documents at once.
- Supported formats:
- PDF
- DOCX
- Automatically processes uploaded documents through an ingestion pipeline.
- Stores uploaded files locally.
- Displays the currently indexed document library.
- Allows indexed documents to be removed from the interface.

### 📄 PDF Processing

DocQue uses several extraction strategies depending on the content of the PDF:

- Native PDF text extraction
- OCR for scanned/image-based PDF pages
- Table extraction
- Embedded image extraction
- Vision-LLM image description

This makes the application useful for more than simple text-only PDFs.

### 🔎 Hybrid Retrieval

DocQue combines two different search approaches:

(1) Semantic/vector search

- Uses BAAI/bge-small-en-v1.5
- Finds passages based on semantic meaning.

(2) Keyword search

- Uses BM25
- Finds passages containing important matching terms.

The results are combined using weighted score fusion.

Default weighting:

Vector similarity: 60%
BM25 keyword search: 40%

### 🎯 Cross-Encoder Reranking

After the initial hybrid retrieval stage, candidate passages can be reranked using:

cross-encoder/ms-marco-MiniLM-L-6-v2

This helps prioritize passages that are more directly relevant to the user's question.

### 💬 Conversational Document Q&A

Users can ask questions naturally, for example:

What are the main conclusions of this report?

What was the total revenue mentioned in the document?

Explain the table on page 5.

Which document contains information about the project deadline?

The application keeps a limited amount of recent conversation history so follow-up questions can be handled in context.

### 📚 Multi-Document Search

The Search tab allows users to search across all indexed documents.

Results are grouped by source document and display:

- File name
- Page number
- Content type
- Retrieved text
- Retrieval score

### 📑 Source Citations

Generated answers include citations such as:

[1]
[2]
[3]

The UI also provides the corresponding:

- File name
- Page number
- Source/unit type
- Text snippet

This makes it easier to trace an answer back to the uploaded documents.

### 🤖 Multiple LLM Providers

DocQue supports two LLM provider modes:

- Google Gemini
- Ollama

This allows the application to work with either a cloud-based model or locally hosted models.


## 🏗️ Architecture

The application follows a RAG pipeline:
```
                    ┌──────────────────────┐
                    │   Upload PDF/DOCX    │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Document Ingestion   │
                    │                      │
                    │ • Text extraction    │
                    │ • OCR                │
                    │ • Tables             │
                    │ • Images             │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │      Chunking        │
                    │                      │
                    │ Token-based chunks   │
                    │ + overlap             │
                    └──────────┬───────────┘
                               │
                               ▼
                 ┌─────────────────────────────┐
                 │       Indexing Layer        │
                 │                             │
                 │ ChromaDB  +  BM25           │
                 └─────────────┬───────────────┘
                               │
                               │
            ┌──────────────────┴──────────────────┐
            │                                     │
            ▼                                     ▼
     Semantic Search                         BM25 Search
     (Embeddings)                            (Keywords)
            │                                     │
            └──────────────────┬──────────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Score Fusion         │
                    │ 60% Vector           │
                    │ 40% BM25             │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Cross-Encoder        │
                    │ Reranking            │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Retrieved Context    │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ LLM Generation       │
                    │ Gemini / Ollama      │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Answer + Citations   │
                    └──────────────────────┘
```

## 🧠 How the RAG Pipeline Works

### 1. Ingestion

When a PDF or DOCX file is uploaded, DocQue extracts useful information from it.

For PDFs, the system can identify:

- Normal text
- Scanned text
- Tables
- Embedded images

Scanned pages are passed through Tesseract OCR.

Images can be passed to a vision-capable LLM to generate textual descriptions.

### 2. Chunking

Large extracted documents are divided into smaller pieces called chunks.

The default configuration is:

Chunk size:       512 tokens
Chunk overlap:     64 tokens
Table chunk size: 1024 tokens

The overlap helps preserve context between neighboring chunks.

### 3. Embeddings

Each chunk is converted into a numerical vector using:

BAAI/bge-small-en-v1.5

These vectors are stored in ChromaDB.

This allows semantic searches such as:

Question:
"What caused the company's profit to decline?"

Document:
"Net income decreased primarily because operating expenses
increased during the reporting period."

Even though the wording is different, semantic retrieval can identify the relevant passage

### 4. BM25 Search

DocQue also performs keyword-based retrieval using BM25.

This is particularly useful when a question contains:

- Specific names
- Technical terms
- Product names
- Numbers
- Exact phrases
- Document-specific terminology

The combination of semantic and keyword retrieval makes the search less dependent on either approach alone.

### 5. Score Fusion

Vector and BM25 scores are normalized and combined.

The default formula is effectively:

Fused Score =
    0.6 × Vector Score
  + 0.4 × BM25 Score

The highest-scoring candidates are passed to the next stage.

### 6. Reranking

The retrieved candidates are then evaluated by the cross-encoder:

cross-encoder/ms-marco-MiniLM-L-6-v2

The reranker considers both:

Question + Retrieved Passage

and produces a relevance score.

The top results are then used as context for the LLM.

### 7. Answer Generation

The LLM receives:

- Recent conversation history
- Retrieved document excerpts
- The user's question

The system prompt instructs the model to:

- Answer only from the supplied context.
- Avoid using outside knowledge.
- Cite factual claims using source numbers.
- Say when the uploaded documents do not contain enough information.
- Avoid guessing or fabricating information.

## 🛠️ Technology Stack
| Component | Technology |
|---|---|
| Frontend / UI | Streamlit |
| RAG architecture | Custom Python pipeline |
| LLM | Google Gemini / Ollama |
| Vector database | ChromaDB |
| Embeddings | Sentence Transformers |
| Embedding model | `BAAI/bge-small-en-v1.5` |
| Keyword retrieval | Rank-BM25 |
| Reranking | Cross-Encoder |
| PDF text extraction | pdfplumber / PyMuPDF |
| OCR | Tesseract |
| DOCX parsing | python-docx |
| Table processing | pandas / pdfplumber / Camelot |
| Tokenization | tiktoken |
| Environment variables | python-dotenv |
| Programming language | Python |

## 📁 Project Structure

A clean repository layout for the application is:
```
DocQue/
│
├── app.py                  # Main Streamlit application (runs at root)
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
│
├── images/                 # App walkthrough screenshots
│   ├── 1.PNG
│   ├── 2.PNG
│   ├── 3.PNG
│   ├── 4.PNG
│   ├── 5.PNG
│   └── 6.PNG
│
├── src/                    # Backend package
│   ├── __init__.py
│   ├── config.py           # Application configuration
│   ├── ingestion.py        # PDF/DOCX ingestion
│   ├── extraction.py       # Cross-document search
│   ├── chunking.py         # Text chunking
│   ├── indexing.py         # ChromaDB + BM25 indexing
│   ├── retrieval.py        # Hybrid retrieval + reranking
│   ├── generation.py       # LLM answer generation
│   ├── llm_client.py       # Gemini/Ollama integration
│   └── memory.py           # Conversation memory
│
├── data/                   # Local data (ignored by git)
│   ├── uploads/
│   └── exports/
│
└── chroma_db/              # Vector stores (ignored by git)
    ├── chroma.sqlite3
    └── bm25_store.pkl
```
## 💻 Requirements

Before running DocQue, install:

- Python 3.10+ recommended
- pip
- Git
- Tesseract OCR
- Ghostscript
- Internet access for downloading Python/model dependencies
- A Gemini API key or a local Ollama installation

###  Hardware

The exact requirements depend heavily on the number and size of documents and the selected models.

For larger document collections, embedding and reranking models can consume significant RAM and CPU/GPU resources.

## 🚀 Installation

### 1. Clone the repository

git clone https://github.com/ARCSunny/DocQue-Document-Q-A-with-RAG
.git

cd DocQue-Document-Q-A-with-RAG


### 2. Create a virtual environment

### Windows

python -m venv venv

venv\Scripts\activate

### macOS / Linux

python3 -m venv venv

source venv/bin/activate

### 3. Install Python dependencies

pip install -r requirements.txt

Some document-processing libraries also require system-level dependencies, especially:

- Tesseract OCR
- Ghostscript

Install those separately according to your operating system.

## 🔐 Configuration

DocQue uses environment variables for model configuration and API credentials.

Create a file named:

.env

Example:

Choose: gemini or ollama

LLM_PROVIDER=gemini

### Gemini

GEMINI_API_KEY=your_api_key_here

GEMINI_MODEL=your_gemini_model


### Ollama

OLLAMA_HOST=http://localhost:11434

OLLAMA_MODEL=llama3.1

OLLAMA_VISION_MODEL=llava


### Retrieval

EMBEDDING_MODEL=BAAI/bge-small-en-v1.5

RERANKER_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2


### OCR

OCR_LANG=eng

⚠️ Never commit your real .env

Your .env file may contain an API key.

Add this to .gitignore:

.env

venv/

__pycache__/

*.pyc


data/uploads/

data/exports/

chroma_db/

Commit a safe template instead:

.env.example

with placeholder values.

### 🤖 Option 1 — Google Gemini

Set:

LLM_PROVIDER=gemini

GEMINI_API_KEY=your_api_key_here

GEMINI_MODEL=your_model_name

The application uses Gemini for:

- Text generation
- Image understanding / image description

A valid Google AI Studio API key is required.

Model names and API quotas can change over time. Use a currently supported Gemini model in your environment rather than assuming an older model name will remain available.

### 🦙 Option 2 — Ollama

If you prefer local models, install Ollama and run the models you want to use.

Example configuration:

LLM_PROVIDER=ollama

OLLAMA_HOST=http://localhost:11434

OLLAMA_MODEL=llama3.1

OLLAMA_VISION_MODEL=llava


Then make sure Ollama is running before launching the application.

The Ollama option can reduce dependence on a cloud LLM API, although local model performance and hardware requirements vary.

## ▶️ Running the Application

From the project root:

streamlit run app.py

Streamlit will start a local development server.

Open the URL displayed in the terminal, typically:

http://localhost:8501

## 📖 How to Use DocQue

### Step 1 — Upload Documents

Open:

📤 Upload & Index

Select one or more:

.pdf
.docx

Then click:

Ingest & Index

DocQue will:
```
Upload
   ↓
Extract
   ↓
OCR if required
   ↓
Extract tables/images
   ↓
Chunk
   ↓
Generate embeddings
   ↓
Store in ChromaDB
   ↓
Build BM25 index
```
### Step 2 — Ask Questions

Open:

💬 Chat

Type a question about your indexed documents.

The application retrieves relevant passages and sends those passages to the configured LLM.

### Step 3 — Inspect Sources

When an answer has citations, expand:

Sources

You can see the source document, page, content type, and a text snippet.

### Step 4 — Search Documents Directly

Open:

🔎 Search

Enter a keyword or phrase.

The application searches across indexed documents and groups matching sections by file.

## 🧩 Main Modules

### ingestion.py

Responsible for extracting information from PDF and DOCX files.

Handles:

- PDF text
- OCR
- PDF tables
- PDF images
- DOCX paragraphs
- DOCX tables
- DOCX embedded images

### chunking.py

Converts extracted raw units into searchable chunks.

It uses token-based splitting with configurable overlap.

### indexing.py

Responsible for storing and maintaining searchable document data.

Uses:

- ChromaDB for vector search
- BM25 for keyword search
- Sentence Transformers for embeddings

It also persists the BM25 index locally.

### retrieval.py

Implements hybrid retrieval.
```
Pipeline:

Query
 ↓
Vector Search
 ↓
BM25 Search
 ↓
Score Normalization
 ↓
Score Fusion
 ↓
Top-K Candidates
 ↓
Cross-Encoder Reranking
 ↓
Top-N Results
```
### generation.py

Responsible for producing the final answer.

It:

(1) Formats retrieved chunks as context.

(2) Adds recent conversation history.

(3) Sends the prompt to the selected LLM.

(4) Builds citation metadata.

(5) Returns the generated answer.

### llm_client.py

Provides a common interface for:

Gemini

Ollama

The rest of the application can call:

complete(...)

without needing to know which LLM provider is currently configured.

It also provides image-description functionality for document images.

### memory.py

Stores recent conversation turns.

The configured memory limit is:

6 conversation turns

This prevents the conversation history from growing indefinitely.

### config.py

Contains configurable application settings such as:

Embedding model

Reranker model

Retrieval top-K

Rerank top-N

Vector/BM25 weights

Chunk size

Chunk overlap

OCR language

OCR DPI

Conversation memory

## ⚙️ Default Retrieval Configuration

The current configuration uses:

Embedding Model:

BAAI/bge-small-en-v1.5

Reranker:

cross-encoder/ms-marco-MiniLM-L-6-v2

Initial retrieval:

Top 20

Final reranked results:

Top 5

Vector weight:

0.60

BM25 weight:

0.40

Chunk size:

512 tokens

Chunk overlap:

64 tokens

Table chunk size:

1024 tokens

These values can be adjusted in config.py or through environment/configuration changes where supported.

## 🗃️ Data Storage

DocQue currently uses local persistent storage.

### Uploaded documents

data/uploads/

### Export directory

data/exports/

### ChromaDB

chroma_db/

### BM25 persistence

chroma_db/bm25_store.pkl

## 🔒 Privacy & Security

DocQue processes uploaded documents locally for extraction and retrieval.

However, when using a cloud LLM such as Gemini, retrieved document context and images may be sent to the configured cloud model for generation or image description.

If privacy is critical, consider using a suitable local LLM through Ollama and review the policies/configuration of every external service you enable.

Security recommendations:

- Never commit .env.
- Never expose API keys in source code.
- Do not commit private documents.
- Do not commit chroma_db/ if it contains private indexed content.
- Use environment variables for credentials.
- Rotate an API key immediately if it is accidentally exposed.

## 🐛 Troubleshooting

### ModuleNotFoundError: No module named 'src'

The application imports modules using:

from src.config import settings

Make sure the Python modules are inside a src/ package and that it contains:

src/__init__.py

Alternatively, change the imports to match a flat project structure.

### Tesseract OCR error

If scanned PDFs cannot be processed, verify that Tesseract OCR is installed and available on your system PATH.

You can test it from a terminal:

tesseract --version

### Camelot / table extraction errors

Some table extraction workflows require Ghostscript.

Verify that Ghostscript is installed and accessible from the system.

### Gemini API errors

Check:

LLM_PROVIDER=gemini

GEMINI_API_KEY=...

GEMINI_MODEL=...


Also verify that:

- The API key is valid.
- The selected model is available to your account.
- You have not exceeded the provider's quota or rate limits.

### Ollama connection error

Verify that Ollama is running and that:

OLLAMA_HOST=http://localhost:11434

matches the actual Ollama server address.

### Slow indexing

Indexing can be CPU/RAM intensive because the application may perform:

- PDF parsing
- OCR
- Image extraction
- Vision-model processing
- Embedding generation
- BM25 indexing

Large PDFs or large document collections can therefore take considerable time.

## 🚧 Known Limitations

The current implementation has several practical limitations:

- OCR currently defaults to English (eng).
- Document indexes are stored locally.
- BM25 data is maintained as a local pickle file.
- Retrieval quality depends on chunk size, embeddings, BM25 weighting, and reranking.
- Large document collections can require substantial RAM and processing time.
- Cloud LLM usage may be subject to API quotas and rate limits.
- DOCX page numbers are not equivalent to physical Word document page numbers because DOCX parsing does not directly preserve rendered page layout.
- Image understanding depends on the selected vision-capable model/provider.
- The application currently focuses on PDF and DOCX rather than supporting every document format.

## 🔮 Future Improvements

Potential improvements include:

- Support more document formats such as TXT, PPTX, XLSX, and HTML.
- Add authentication and user accounts.
- Add document-level permissions.
-Add persistent chat sessions.
- Add conversation export.
- Add streaming LLM responses.
- Improve table-aware retrieval.
- Improve multilingual OCR.
- Add configurable retrieval weights through the UI.
- Add document metadata filters.
- Add document preview.
- Add page-level PDF preview for citations.
- Add evaluation datasets for measuring retrieval quality.
- Add automated RAG evaluation metrics.
- Add GPU acceleration where available.
- Add Docker support.
- Add automated tests and CI/CD.
- Improve duplicate-document detection.
- Add database-backed user/document management.

## 📸 App Walkthrough

Here is a quick look at DocQue in action:

### 1. Upload & Index Documents
Easily drag and drop PDF or DOCX files. The app parses native text, scanned pages via OCR, tables, and even extracts insights from embedded charts/images.

![image alt](https://github.com/ARCSunny/DocQue-Document-Q-A-with-RAG/blob/b26fe489d9d1f9a7ad4060dd856989cfd3644485/images/upload-tab.PNG)

### 2. Document Management
View all your indexed documents at a glance and delete any file instantly if needed.

![image alt](https://github.com/ARCSunny/DocQue-Document-Q-A-with-RAG/blob/f6e3fe90ee4a362b85bae9a5e8cc54e1a83eb149/images/document-parsing.PNG)

### 3. Targeted Chat & Document Filtering
Ask questions about your documents in a ChatGPT-like interface. You can optionally filter your queries to search only specific files using the settings expander.

![image alt](https://github.com/ARCSunny/DocQue-Document-Q-A-with-RAG/blob/f6e3fe90ee4a362b85bae9a5e8cc54e1a83eb149/images/doc-filter.PNG)

### 4. Interactive Q&A and Response Generation
Get detailed, natural-language responses backed by context-aware analysis of your uploaded files.

![image alt](https://github.com/ARCSunny/DocQue-Document-Q-A-with-RAG/blob/f6e3fe90ee4a362b85bae9a5e8cc54e1a83eb149/images/chat-interface.PNG)

### 5. Transparent Citations
Every assistant response comes with expandable source citations showing the exact file name, page number, and text snippet used to generate the answer.

![image alt](https://github.com/ARCSunny/DocQue-Document-Q-A-with-RAG/blob/f6e3fe90ee4a362b85bae9a5e8cc54e1a83eb149/images/citations.PNG)

### 6. Cross-Document Search
Quickly find specific phrases, data points, or concepts across your entire document library without having to chat, complete with relevance scores and page previews.

![image alt](https://github.com/ARCSunny/DocQue-Document-Q-A-with-RAG/blob/f6e3fe90ee4a362b85bae9a5e8cc54e1a83eb149/images/search-tab.PNG)

## ⭐ If You Find This Project Useful

If this project helps you learn about RAG, document processing, semantic search, or LLM applications, consider giving the repository a ⭐ on GitHub.

Built with Python, Streamlit, ChromaDB, Sentence Transformers, BM25, and modern LLM tooling.
