# ARCHITECTURE.md — System Architecture & Technical Design

## 1. Architecture Overview

The system is split into two pipelines, matching standard RAG (Retrieval-Augmented Generation) design:

- **Ingestion pipeline (batch/offline)**: runs once per document. PDF → OCR → language ID → chunk → embed → store. Also produces the summary.
- **Query pipeline (live)**: runs on every user question. Question → embed → retrieve → (rerank) → LLM generates a grounded, cited answer.

```
INGESTION PIPELINE
==================
PDF Corpus ──▶ OCR + Layout ──▶ Language ID ──▶ Chunking ──▶ Embeddings ──▶ Vector Store
(local files)   (Sarvam Vision)  (local)         (local)      (local GPU)    (ChromaDB, local)
                       │
                       └──▶ Summarizer (Sarvam-30B API) ──▶ <file>_summary.md saved next to PDF

QUERY PIPELINE
==============
User Question ──▶ Embed (local) ──▶ Retrieve top-k (ChromaDB) ──▶ Rerank (local) ──▶
   ──▶ Sarvam-105B API (answer + reasoning over retrieved chunks) ──▶ Answer + Citations ──▶ Streamlit UI
```

## 2. Components

### 2.1 Ingestion & OCR (`src/ingestion/`)
- **`pdf_splitter.py`**: Splits any PDF exceeding Sarvam's 10-page/job limit into sub-batches; tracks original page numbers so citations remain accurate after reassembly.
- **`ocr_client.py`**: Thin wrapper around the Sarvam Document Intelligence API (`sarvamai` SDK). Handles job creation, upload, polling, download, and retries. Returns clean Markdown/HTML per document with tables preserved and reading order intact.
- **`language_detect.py`**: Tags each page/chunk with a detected language (English/Hindi/other) using a local, free library (`langdetect` or `fasttext`). Used to route summary language and to help interpret Hindi/English mixed content.

### 2.2 Processing (`src/processing/`)
- **`chunker.py`**: Splits structured document text into retrieval-sized chunks (~300-800 words), preferring natural boundaries (numbered clauses, section headings) over arbitrary character counts. Each chunk carries metadata: `source_file`, `page_number`, `section_heading` (if detected), `chunk_id`.
- **`summarizer.py`**: Sends full (or map-reduced, for very long documents) document text to the Sarvam-30B API with a structured prompt (see Data Contracts below). Writes output to `<filename>_summary.md` next to the source PDF. Includes a lightweight self-check: extracts key numbers from the generated summary and verifies they appear in the source text before saving.

### 2.3 Retrieval (`src/retrieval/`)
- **`embeddings.py`**: Wraps `sentence-transformers` with the `BAAI/bge-m3` multilingual model. Runs on GPU (RTX 3050) when available, falls back to CPU. Used both at ingestion time (embedding chunks) and query time (embedding the user's question).
- **`vector_store.py`**: Wraps ChromaDB. One persistent local collection holding all chunks; each chunk's metadata includes `source_file`, enabling both "search everything" and "search this one document" queries via a metadata filter (`where={"source_file": ...}`).
- **`reranker.py`** *(optional, stretch goal)*: Wraps a small local cross-encoder (`bge-reranker-base`) to re-score the top-N retrieved chunks against the question before passing the best few to the LLM.

### 2.4 Chatbot (`src/chatbot/`)
- **`rag_chain.py`**: Orchestrates the query pipeline — embed question, retrieve (optionally filtered to one document), rerank, build a grounded prompt, call the Sarvam-105B API, and attach citation metadata to the returned answer. All Sarvam API calls (chat + document intelligence) go through a single wrapper so the model/provider can be swapped later without touching calling code.

### 2.5 Application (`app/`)
- **`streamlit_app.py`**: The user-facing interface — document browser, summary viewer, and chat interface with a toggle for "search all documents" vs. "search this document only." This is the only component end users (officials, mentors) interact with directly.

### 2.6 Orchestration (`scripts/`)
- **`run_pipeline.py`**: CLI entry point that runs the full ingestion pipeline over a directory of PDFs — OCR → chunk → embed → store → summarize — with per-document error handling (a failure on one file logs and continues, never crashes the batch).

## 3. Folder / File Structure

```
doc-intelligence-mvp/
├── PRD.md
├── ARCHITECTURE.md
├── RULES.md
├── PHASES.md
├── MEMORY.md
├── README.md
├── .env.example
├── .gitignore
├── requirements.txt
├── config.py                     # central config: paths, model names, thresholds
├── data/
│   ├── raw_pdfs/                 # input PDFs (mirrors real folder structure)
│   ├── processed/                # OCR'd structured text (Markdown), per document
│   └── summaries/                # (or saved directly next to source PDF — see RULES.md)
├── src/
│   ├── ingestion/
│   │   ├── pdf_splitter.py
│   │   ├── ocr_client.py
│   │   └── language_detect.py
│   ├── processing/
│   │   ├── chunker.py
│   │   └── summarizer.py
│   ├── retrieval/
│   │   ├── embeddings.py
│   │   ├── vector_store.py
│   │   └── reranker.py
│   ├── chatbot/
│   │   └── rag_chain.py
│   └── utils/
│       └── logger.py
├── app/
│   └── streamlit_app.py
├── scripts/
│   └── run_pipeline.py
└── tests/
    └── test_ocr_client.py
```

## 4. Technology Stack

| Layer | Tool | Runs where |
|---|---|---|
| PDF handling & splitting | PyMuPDF / pypdf | Local |
| OCR + layout + tables | Sarvam Document Intelligence API | Cloud API |
| Language identification | fastText / langdetect | Local |
| Chunking | Custom / LangChain text splitters | Local |
| Embeddings | BAAI/bge-m3 (multilingual) | Local — GPU (RTX 3050) |
| Retrieval re-ranking | bge-reranker-base (optional) | Local — GPU (RTX 3050) |
| Vector database | ChromaDB | Local |
| Summarization + chat LLM | Sarvam-30B / Sarvam-105B | Cloud API |
| Application interface | Streamlit | Local |
| Orchestration | Python 3.11+ | Local |

## 5. Data Contracts

These shapes are fixed early so components can be built and tested independently against mock data.

### 5.1 Chunk record (stored in ChromaDB)
```json
{
  "chunk_id": "order_2026_045__p3__c1",
  "text": "...",
  "source_file": "order_2026_045.pdf",
  "page_number": 3,
  "section_heading": "Financial Implications",
  "language": "hi",
  "embedding": [0.0123, -0.0456, ...]
}
```

### 5.2 Document summary output
```json
{
  "source_file": "order_2026_045.pdf",
  "language": "hi",
  "purpose": "...",
  "key_decisions": ["..."],
  "dates": ["..."],
  "amounts": ["..."],
  "responsible_departments": ["..."],
  "action_items": ["..."],
  "not_found_fields": ["amounts"]
}
```

### 5.3 Chat response (returned to the UI)
```json
{
  "answer_text": "...",
  "citations": [
    {"source_file": "order_2026_045.pdf", "page_number": 3, "snippet": "..."}
  ],
  "mode": "general" 
}
```
`mode` is either `"general"` (searched across all documents) or `"document_specific"` (filtered to one `source_file`).

## 6. Configuration & Secrets
- All API keys (`SARVAM_API_KEY`) live in a local `.env` file, loaded via `python-dotenv`. Never hardcoded, never committed (see `.gitignore`).
- `config.py` centralizes: model names, chunk size/overlap, top-k retrieval count, file paths, and the OCR page-split threshold (10 pages/job) — so these are changed in one place, not scattered across files.

## 7. Deployment Model (MVP)
Single-machine, local execution only. No containerization, no cloud hosting, no multi-user concerns for this phase. `scripts/run_pipeline.py` is run manually (or on a simple schedule) to process new PDFs; `app/streamlit_app.py` is run locally (`streamlit run app/streamlit_app.py`) for the interactive demo.

## 8. Scalability Notes (for the mentor-facing report — not built in the MVP)
- **Vector database**: ChromaDB (local file) → Qdrant / Milvus / pgvector (server-based) — same query pattern, swap the client.
- **LLM access**: already isolated behind `rag_chain.py` and `summarizer.py` — switching to a self-hosted model later changes one function, not the calling code.
- **Processing**: single-script pipeline now → job queue (Celery / Airflow) for higher document volume later.
