# Copilot Instructions for this Repository

GitHub Copilot: read these files, in this order, before writing or modifying any code in this repository. They are the source of truth for this project — follow them over general defaults.

1. **`/RULES.md`** — hard constraints (approved libraries, error handling, cost awareness, what NOT to do). If any request conflicts with this file, flag the conflict instead of silently overriding it.
2. **`/PRD.md`** — what is being built and why, functional requirements, and explicit non-goals.
3. **`/ARCHITECTURE.md`** — system design, folder structure, tech stack, and the exact data shapes (chunk, summary, chat response) that every component must conform to.
4. **`/PHASES.md`** — the current build order. Do not build ahead of the current phase (e.g. don't start the chatbot before ingestion + summarization work). Check `/MEMORY.md` to see which phase is active.
5. **`/MEMORY.md`** — current project status. Read the "Current Status" section at the top before starting work, and update it (or ask the developer to) at the end of the session.

## Quick Rules Summary
- Stack is fixed: Sarvam API (OCR + LLM), `bge-m3` embeddings (local), ChromaDB (local), Streamlit UI. Don't substitute without asking.
- Never fabricate facts in summaries or chatbot answers — ground everything in retrieved/extracted document text.
- Never crash a batch job on a single document's failure — catch, log, continue.
- Never hardcode or print API keys — use `.env` via `python-dotenv`.
- Don't add new dependencies outside `requirements.txt` without noting why in `MEMORY.md`.
