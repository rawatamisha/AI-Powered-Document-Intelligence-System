# MEMORY.md — Running Project Memory

**Purpose**: This file is the agent's memory across chat sessions/restarts. Update it at the end of every working session — that way, a fresh chat with the coding agent only needs to read this file (not the whole codebase) to know exactly where things stand. Keep entries short and factual; this is a status log, not documentation (that's what `ARCHITECTURE.md` is for).

**How to use this file (for the developer)**:
1. At the start of a new agent session, paste or point the agent to this file first, along with `RULES.md`.
2. At the end of a session, ask the agent (or do it yourself) to append a new dated entry below, following the template.
3. Never delete old entries — this is a log. If something becomes outdated, note the correction in a new entry rather than editing history.

---

## How to Write an Entry
```
## [YYYY-MM-DD] — Session N
**Phase**: <current phase from PHASES.md>
**Completed**:
- ...
**In Progress**:
- ...
**Decisions Made**:
- ...
**Blockers / Open Questions**:
- ...
**Files Changed**:
- ...
**Next Session Should**:
- ...
```

---

## Current Status (keep this section updated at the top — most recent snapshot)
**Phase**: Phase 2 — Chunking, Embeddings & Summarization
**Last Updated**: 2026-07-22
**Overall Progress**: Phase 2 pipeline now runs end-to-end on the sample PDF: OCR text is chunked, indexed in ChromaDB, and summarized with a safe fallback if Sarvam returns malformed output.

---

## Session Log

## [Not yet started] — Session 0 (Planning)
**Phase**: Phase 0 — Project Setup
**Completed**:
- PRD.md, ARCHITECTURE.md, RULES.md, PHASES.md written and finalized.
- Repo folder structure created.
- Tech stack decided: Sarvam AI (OCR + Sarvam-30B/105B), bge-m3 embeddings (local), ChromaDB (local), Streamlit UI.
- Hardware confirmed sufficient: Dell G15 5530, i5-13450HX, RTX 3050 6GB, 16GB RAM.
- Cost model confirmed: ₹0.50/page OCR (flat rate, applies at MVP stage too, no separate "production" pricing); ₹100 free signup credit ≈ 200 free pages.
- Decision: proceeding fully solo — not integrating with teammate (Member 2/3) components for this MVP, despite some task overlap (OCR, chunking, embeddings). May revisit integration later if the team merges submissions.
**In Progress**: Nothing yet — about to begin Phase 0 setup tasks.
**Decisions Made**:
- Solo build, full pipeline owned end-to-end (not splitting into "Member 1 only" scope).
- GitHub Copilot agent chosen as the primary coding agent, working locally (not GCP) in VS Code.
**Blockers / Open Questions**: None currently.
**Files Changed**: N/A (planning phase only).
**Next Session Should**: Start Phase 0 — set up folder structure, `requirements.txt`, `.env.example`, `config.py`, and `logger.py`; verify Sarvam API key and GPU both work before writing any pipeline logic.

---

<!-- Add new dated entries above this line as work progresses. -->

## [2026-07-22] — Session 2
**Phase**: Phase 2 — Chunking, Embeddings & Summarization
**Completed**:
- Implemented language detection, chunking, local embeddings, ChromaDB storage, and structured summarization.
- Updated the pipeline so already-OCR'd PDFs still continue through Phase 2 work.
- Added regression tests for the new Phase 2 modules.
- Verified the sample PDF completes Phase 2 end-to-end and writes a summary file.
**In Progress**:
- Phase 2 is operational on the sample set; summary quality can be reviewed on more PDFs next.
**Decisions Made**:
- Treat malformed Sarvam summary output as retryable, then fall back to a safe non-fabricated summary if retries are exhausted.
- Do not skip Phase 2 just because OCR output already exists.
**Blockers / Open Questions**:
- Sarvam summary responses can still be inconsistent, so the fallback path remains necessary for reliability.
**Files Changed**:
- `scripts/run_pipeline.py`
- `src/ingestion/language_detect.py`
- `src/processing/chunker.py`
- `src/processing/summarizer.py`
- `src/retrieval/embeddings.py`
- `src/retrieval/vector_store.py`
- `tests/test_language_detect.py`
- `tests/test_chunker.py`
- `tests/test_embeddings.py`
- `tests/test_vector_store.py`
- `tests/test_summarizer.py`
**Next Session Should**:
- Review the generated summary quality on additional PDFs, then move on to Phase 3 retrieval/chatbot work.

## [2026-07-21] — Session 1
**Phase**: Phase 0 — Project Setup
**Completed**:
- venv created, dependencies installed
- Sarvam API key configured in .env
- GPU verified: RTX 3050 6GB detected, torch.cuda.is_available() = True
  (required installing torch via cu126 wheel — plain `pip install torch` gives CPU-only)
- Repo pushed to GitHub (private): govdoc-intelligence
**Next Session Should**: Begin Phase 2 — implement src/processing/chunker.py per ARCHITECTURE.md §2.2/§5.1

## [2026-07-22] — Session 1
**Phase**: Phase 0 — Project Setup
**Completed**:
- Debugged the phase 0
- solved the issue of 
    "<!-- page: 1 -->
    [OCR FAILED for pages 1-1 — needs manual review]"
- completed phase 2 processes

**Next Session Should**: Begin Phase 2 — implement src/processing/chunker.py per ARCHITECTURE.md §2.2/§5.1