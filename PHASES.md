# PHASES.md — Phase-Wise Build Plan

Build strictly in this order. Do not start a phase until the previous phase's "Definition of Done" is met — each phase depends on working output from the one before it. When starting a new agent session, tell the agent which phase you're on and point it to `MEMORY.md` for current status before asking it to write code.

---

## Phase 0 — Project Setup (½ day)
**Goal**: A working, empty skeleton with dependencies installed and config wired up.

Tasks:
- [ ] Create the folder structure exactly as defined in `ARCHITECTURE.md` §3.
- [ ] `requirements.txt` with pinned versions of all approved libraries.
- [ ] `.env.example` with placeholder `SARVAM_API_KEY=your_key_here`.
- [ ] `.gitignore` covering `.env`, `data/raw_pdfs/*`, `__pycache__/`, `*.pyc`, model cache folders.
- [ ] `config.py` with paths, model names, chunk size, top-k, and OCR page-split threshold as constants.
- [ ] `src/utils/logger.py` — a single shared logger used by every module.
- [ ] Confirm Sarvam API key works with a trivial test call.
- [ ] Confirm `bge-m3` downloads and runs on GPU (`torch.cuda.is_available()` check).

**Definition of Done**: `python -c "import config; print('ok')"` runs with no errors; a one-line Sarvam API test script successfully returns a response; GPU is detected.

---

## Phase 1 — Ingestion & OCR (Week 1)
**Goal**: Any PDF in `data/raw_pdfs/` becomes clean, structured, page-tagged text.

Tasks:
- [ ] `pdf_splitter.py`: split PDFs over 10 pages into sub-batches; track original page numbers.
- [ ] `ocr_client.py`: Sarvam Document Intelligence API wrapper — create job, upload, poll, download, retry on failure (see `RULES.md` §4).
- [ ] `language_detect.py`: tag extracted text by language (en/hi/other).
- [ ] Reassembly logic: stitch multi-batch OCR output back into one document, preserving page numbers.
- [ ] Test on 2-3 sample PDFs (mixed English/Hindi, at least one with a table) before running on the full sample set.
- [ ] Save structured output to `data/processed/<filename>.md`.

**Definition of Done**: Running the ingestion step on the full sample document set (~15-20 PDFs) produces a structured Markdown file per PDF in `data/processed/`, with tables intact and page numbers preserved, and zero unhandled crashes on the batch. Update `MEMORY.md`.

---

## Phase 2 — Chunking, Embeddings & Summarization (Week 2)
**Goal**: Every document is summarized (saved next to the source PDF) and indexed for search.

Tasks:
- [ ] `chunker.py`: section-aware chunking (~300-800 words/chunk) with metadata (`source_file`, `page_number`, `section_heading`).
- [ ] `embeddings.py`: `bge-m3` wrapper, GPU-accelerated, batch encoding of chunks.
- [ ] `vector_store.py`: ChromaDB wrapper — add chunks with metadata, support filtered queries by `source_file`.
- [ ] `summarizer.py`: prompt-engineered Sarvam-30B call producing the structured summary (see `ARCHITECTURE.md` §5.2 for the exact output shape); write to `<filename>_summary.md` next to the source PDF.
- [ ] Add the self-check step: extract key numbers/dates from the generated summary and verify they appear in the source text; flag mismatches instead of silently saving.
- [ ] Run on the full sample set; manually review at least 5 summaries against their source PDFs for factual accuracy.

**Definition of Done**: Every sample PDF has a summary file saved next to it with zero fabricated facts (manually verified); all chunks are searchable in ChromaDB by both "all documents" and "single document" queries. Update `MEMORY.md`.

---

## Phase 3 — RAG Chatbot & UI (Week 3)
**Goal**: A working chat interface that answers questions with citations, in both general and document-specific mode.

Tasks:
- [ ] `rag_chain.py`: embed question → retrieve top-k from ChromaDB (optionally filtered) → (optional) rerank → build grounded prompt → call Sarvam-105B → return `{answer_text, citations, mode}` per the data contract.
- [ ] *(Optional/stretch)* `reranker.py`: add `bge-reranker-base` re-scoring before the top chunks go to the LLM.
- [ ] `streamlit_app.py`: document browser + summary viewer, chat interface with a toggle for "search all documents" vs. "this document only," and citations rendered under each answer.
- [ ] Build a small test set of ~15-20 questions (mix of general and document-specific, with known correct answers) and check the chatbot against it.

**Definition of Done**: The Streamlit app runs locally, answers both general and document-specific questions correctly on at least 80% of the test question set, and every answer displays a source file + page citation. Update `MEMORY.md`.

---

## Phase 4 — Testing, Cost Analysis & Report (Week 4)
**Goal**: A tested, documented MVP ready to present to mentors.

Tasks:
- [ ] Run the full pipeline on a larger/messier batch of documents (including any edge cases: scanned-only PDFs, heavy tables, mixed-language pages).
- [ ] Record actual API usage (pages processed, tokens used) against the free credit balance; compute real per-document and per-query cost.
- [ ] Fill in the cost/scalability section of the project report using real measured numbers rather than estimates.
- [ ] Fix any bugs found during the larger test run.
- [ ] Final pass on `README.md` so the repo is understandable to someone who wasn't in the room for the build (i.e. the mentor team).
- [ ] Prepare the demo flow: which documents to show, which questions to ask live.

**Definition of Done**: Full pipeline runs end-to-end on the larger test batch without manual intervention; cost analysis in the report reflects real, measured numbers; demo is rehearsed.

---

## Out-of-Order Work (do not do early)
- Reranker (Phase 3) is optional — skip it first, add it only if retrieval quality needs improvement and time allows.
- Do not start UI work (Phase 3) before Phase 2's summaries and vector store are working — there's nothing meaningful to display otherwise.
- Do not attempt production-scale concerns (auth, multi-user, containerization) — explicitly out of scope per `PRD.md`.
