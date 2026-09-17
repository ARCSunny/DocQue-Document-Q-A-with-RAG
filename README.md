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

🔎 Hybrid Retrieval

DocQue combines two different search approaches:

Semantic/vector search

Uses BAAI/bge-small-en-v1.5

Finds passages based on semantic meaning.

Keyword search

Uses BM25

Finds passages containing important matching terms.

The results are combined using weighted score fusion.

Default weighting:

Vector similarity: 60%
BM25 keyword search: 40%

🎯 Cross-Encoder Reranking

After the initial hybrid retrieval stage, candidate passages can be reranked using:

cross-encoder/ms-marco-MiniLM-L-6-v2

This helps prioritize passages that are more directly relevant to the user's question.

💬 Conversational Document Q&A

Users can ask questions naturally, for example:

What are the main conclusions of this report?

What was the total revenue mentioned in the document?

Explain the table on page 5.

Which document contains information about the project deadline?

The application keeps a limited amount of recent conversation history so follow-up questions can be handled in context.

📚 Multi-Document Search

The Search tab allows users to search across all indexed documents.

Results are grouped by source document and display:

File name

Page number

Content type

Retrieved text

Retrieval score

📑 Source Citations

Generated answers include citations such as:

[1]
[2]
[3]

The UI also provides the corresponding:

File name

Page number

Source/unit type

Text snippet

This makes it easier to trace an answer back to the uploaded documents.

🤖 Multiple LLM Providers

DocQue supports two LLM provider modes:

Google Gemini

Ollama

This allows the application to work with either a cloud-based model or locally hosted models.

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


