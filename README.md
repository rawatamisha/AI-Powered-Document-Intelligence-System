# AI-Powered Document Intelligence Platform (MVP)

Multilingual summarization and RAG chatbot for government PDF documents — 4-week internship MVP.

## Start Here (for both humans and AI coding agents)
Read these in order before touching code:
1. `PRD.md` — what we're building and why
2. `ARCHITECTURE.md` — how it's built, tech stack, folder structure, data shapes
3. `RULES.md` — hard constraints for any code written in this repo
4. `PHASES.md` — the build order (don't skip ahead)
5. `MEMORY.md` — current status; update at the end of every session

## Setup
```bash
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env        # then add your real SARVAM_API_KEY
```

## Running the Pipeline
```bash
# Process all PDFs in data/raw_pdfs/ -> summaries + searchable index
python scripts/run_pipeline.py

# Launch the chat/summary UI
streamlit run app/streamlit_app.py
```

## Hardware Target
Developed and tested on: Dell G15 5530, Intel i5-13450HX, RTX 3050 6GB VRAM, 16GB RAM.
Embeddings and reranking run locally on GPU; OCR and LLM calls go through the Sarvam AI API — see `ARCHITECTURE.md` §1 for why.

## Status
See `MEMORY.md` → "Current Status" for exactly where the build stands right now.
