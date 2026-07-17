# RULES.md — Rules of Engagement for the AI Coding Agent

This file sets hard boundaries for any AI agent (GitHub Copilot agent, Claude Code, etc.) working on this repository. Read this before writing or modifying any code. If a request conflicts with this file, this file wins — flag the conflict to the developer instead of silently overriding it.

## 1. Tech Stack — Do Not Substitute Without Asking
The stack is fixed by `ARCHITECTURE.md`. Do not swap any of the following for an alternative, even if you believe it's "better," without explicitly asking the developer first:
- OCR: **Sarvam Document Intelligence API** (not Tesseract, not a different OCR provider)
- Embeddings: **BAAI/bge-m3** via `sentence-transformers`
- Vector store: **ChromaDB**
- LLM: **Sarvam-30B** (summarization) / **Sarvam-105B** (chat) via the Sarvam API
- UI: **Streamlit**

If a library listed above turns out to be broken/unavailable, stop and report the issue rather than silently switching to a different tool.

## 2. Approved Libraries
Default to these; adding a new dependency beyond this list requires a one-line note in `MEMORY.md` explaining why.
- `sarvamai` — Sarvam API SDK
- `chromadb`
- `sentence-transformers`
- `streamlit`
- `pymupdf` (fitz) or `pypdf` — PDF handling
- `langdetect` or `fasttext` — language ID
- `python-dotenv` — secrets/config loading
- `tenacity` — retry/backoff logic for API calls
- `pydantic` — data contract validation (optional but encouraged for the schemas in `ARCHITECTURE.md`)
- Standard library: `logging`, `pathlib`, `json`, `dataclasses`

**Avoid** unless explicitly requested: heavyweight orchestration frameworks (LangChain's full agent stack, LlamaIndex, etc. — the pipeline here is simple enough to write directly), pandas (not needed for this data shape), any additional cloud SDKs beyond Sarvam, any GUI framework other than Streamlit.

## 3. API Key & Secrets Handling
- API keys are read only from environment variables (via `.env` + `python-dotenv`). Never hardcode a key in any file.
- Never print, log, or include an API key in any output, error message, or commit.
- `.env` must be listed in `.gitignore` and never committed. Only `.env.example` (with placeholder values) is committed.

## 4. Error Handling Standards
- **Never let one document's failure crash the batch.** Every per-document operation (OCR call, summarization call, embedding) must be wrapped so that an exception is caught, logged with the filename and error, and the pipeline moves to the next document.
- **No silent failures.** Every caught exception must be logged (via `src/utils/logger.py`), not just passed or ignored.
- **Retries for API calls**: Sarvam API calls (OCR and LLM) should retry on transient errors (timeouts, 5xx, rate limits) using exponential backoff (`tenacity`), with a sane max retry count (e.g. 3) — do not retry indefinitely.
- **Timeouts**: every external API call must have an explicit timeout; never leave a call unbounded.

## 5. Data Accuracy Rules (non-negotiable — this is a government document project)
- The summarizer must never fabricate a fact, number, date, or name. If a requested field isn't found in the source text, the output must explicitly say so (see `not_found_fields` in the data contract) rather than guess or infer.
- The chatbot must answer only from retrieved chunks. It must not use general world knowledge to fill gaps in an answer about document content.
- Every chatbot answer must carry citation metadata (source file + page number) that comes from retrieval, never from the LLM guessing a reference.
- Never modify, overwrite, delete, or rename the original source PDFs. All generated output (summaries, processed text) is written to separate files/locations.

## 6. Cost Awareness
- Sarvam API usage is billed (₹0.50/page OCR; per-token LLM pricing) against a limited free credit balance. Do not write code that calls the OCR or LLM API in a loop without an explicit, deliberate trigger (e.g. no auto-retry-on-every-keystroke, no accidental re-processing of already-processed documents).
- Before running a full-batch pipeline test, prefer testing on 1-2 sample documents first.
- `run_pipeline.py` must skip documents that have already been processed (check for an existing summary/output file) unless a `--force` flag is passed.

## 7. Code Style
- Python 3.11+, type hints on all function signatures.
- Follow PEP 8; format with `black` if available.
- Functions should be small and single-purpose — a function that "does OCR" should not also handle chunking.
- Docstrings on every public function explaining purpose, inputs, and outputs (this matters more than usual here, since the code is also project documentation for the mentor report).
- No global mutable state; pass configuration explicitly or via `config.py` constants.

## 8. Testing
- Any new module in `src/` should have at least a minimal test in `tests/` — even a simple "does this function return the expected shape given mock input" test.
- Do not require live API calls for tests to pass — mock the Sarvam API responses where practical, so tests can run without spending credits.

## 9. What the Agent Should NOT Do
- Do not modify `PRD.md`, `ARCHITECTURE.md`, or `PHASES.md` without being explicitly asked — these reflect decisions already made with the mentor team.
- Do not attempt to self-host or download the Sarvam-30B/105B model weights locally — this MVP uses the API only (the laptop's 6GB VRAM cannot serve these models; see `ARCHITECTURE.md` §8 for the future self-hosting note).
- Do not introduce authentication, multi-user, or access-control features — explicitly out of scope (see `PRD.md` §6).
- Do not restructure the folder layout defined in `ARCHITECTURE.md` without updating that file to match.
- Do not commit `.env`, API keys, downloaded model weight files, or the contents of `data/raw_pdfs/` (real government documents should not go into version control — add to `.gitignore`).

## 10. Session Handoff
At the end of any working session, update `MEMORY.md` with what was completed, what's in progress, and any decisions made — see `MEMORY.md` for the exact format. This is how continuity is maintained across chat sessions/agent restarts without re-reading the whole codebase.
