# PRD.md — Project Requirements Document

## 1. Project Name
**AI-Powered Document Intelligence Platform** (working title) — a multilingual summarization and RAG chatbot MVP for government document repositories.

## 2. One-Line Summary
Turn a folder of lengthy, multilingual government PDFs (orders, meeting minutes, reports) into (a) an accurate summary saved next to each file, and (b) a chatbot that answers questions about them with source references.

## 3. Background & Problem Statement
The ministry produces a large and growing volume of PDF documents — orders, meeting minutes, circulars, reports — containing text, tables, and charts, written in English, Hindi, and occasionally other Indian regional languages. Documents are long and dense. Officials currently have no fast way to:
- Understand what a document contains without reading it in full.
- Search across many documents for specific information.
- Get an answer to a question with a verifiable source, rather than having to hunt through PDFs manually.

This project is a 4-week solo MVP, built as an internship deliverable, intended to prove the approach works and to give mentor scientists a working reference implementation they can later scale onto production infrastructure.

## 4. Target Users
- **Primary**: Ministry officials / officers who need to quickly understand or search documents, without technical background. They interact only with the summaries and the chatbot UI — never with code or raw pipeline output.
- **Secondary**: Mentor scientists evaluating the prototype for scalability, architecture soundness, and feasibility of a production rollout.
- **Developer/owner**: The intern (solo), building and maintaining the system during the MVP phase.

## 5. Goals
1. Produce a **precise, data-accurate** summary for every ingested PDF, saved next to the original file.
2. Provide a chatbot that can:
   - Answer general questions using the entire document corpus.
   - Answer questions scoped to a single, specified document.
   - Return the source document and page number alongside every answer.
3. Run entirely on the developer's laptop (Dell G15 5530, i5-13450HX, RTX 3050 6GB, 16GB RAM) with **zero or near-zero cost**, using free/open-source local components plus the Sarvam AI free credit tier.
4. Be architected so mentor scientists can scale the same design onto production infrastructure without a redesign (see `ARCHITECTURE.md`).
5. Be fully documented, so the 4-week build can be explained and defended in a project report.

## 6. Non-Goals (explicitly out of scope for the MVP)
- Multi-user authentication, role-based access control, or classification/clearance enforcement (may be relevant for a future production version, not this MVP).
- Production-grade deployment (Docker/Kubernetes, cloud hosting, load balancing).
- Self-hosting the LLM (Sarvam-30B/105B) — MVP uses the hosted API only.
- Real-time ingestion of new documents (a manual "run pipeline" step is acceptable for MVP).
- Support for languages beyond English, Hindi, and best-effort handling of other Indian regional languages present in the sample set.
- Editing or modifying source PDFs in any way.

## 7. Functional Requirements

### FR1 — Document Summarization
- **FR1.1**: For every PDF placed in the input directory, the system generates a structured summary (purpose, key decisions, dates, amounts, responsible departments, action items).
- **FR1.2**: The summary is saved as a separate file (e.g. `<filename>_summary.md`) in the same folder as the source PDF.
- **FR1.3**: The summary must not contain any fact, number, date, or name not present in the source document. If information is not present, the summary must state "not found in document" for that field rather than infer or guess.
- **FR1.4**: Summary language matches the source document's primary language (English or Hindi), unless configured otherwise.
- **Acceptance criteria**: Given 10 sample documents, a human reviewer can verify every factual claim in each summary against the source PDF with zero contradictions.

### FR2 — General Q&A (cross-document)
- **FR2.1**: A user can ask a natural-language question and receive an answer synthesized from the most relevant chunks across the entire document corpus.
- **FR2.2**: The answer must be grounded only in retrieved content — no fabricated claims.
- **Acceptance criteria**: For a held-out test set of questions with known answers, retrieval returns the correct source document in the top 5 results at least 80% of the time.

### FR3 — Document-Specific Q&A
- **FR3.1**: A user can select or specify a single document and ask questions scoped only to that document's content.
- **FR3.2**: The system must not pull in content from other documents when a specific document is selected.

### FR4 — Citations / References
- **FR4.1**: Every chatbot answer includes the source filename and page number(s) for each claim it makes.
- **FR4.2**: References are derived from retrieval metadata (not generated/guessed by the LLM).

## 8. Non-Functional Requirements
- **Accuracy over fluency**: A shorter, correct answer is always preferred to a longer, unverified one.
- **Cost**: MVP build and demo must stay within Sarvam AI's free signup credit (~₹100 / ~200 OCR pages at current pricing). Any paid usage must be deliberate and logged.
- **Hardware**: Must run on the specified laptop (16GB RAM, RTX 3050 6GB VRAM) without external compute.
- **Language coverage**: English and Hindi are first-class; other Indian regional languages are best-effort (dependent on Sarvam Vision's coverage).
- **Latency**: Not a hard requirement for MVP — a chatbot response within ~10-15 seconds is acceptable.
- **Reliability**: A failure processing one document must not crash the batch — errors are logged and the pipeline continues with the next document.

## 9. Success Metrics
- 100% of sample PDFs produce a saved summary file with no fabricated facts (verified by manual review).
- Chatbot correctly answers at least 80% of a prepared test question set (mix of general and document-specific), with correct citations.
- End-to-end pipeline (ingest → OCR → summarize → index) completes on a batch of ~20 documents without manual intervention.
- Full working demo deliverable at end of Week 4, with cost and scalability analysis documented.

## 10. Assumptions & Constraints
- Solo developer, 4-week timeline, working independently (not relying on teammates' components — see `MEMORY.md` for any decisions on this).
- Documents are readable PDFs (scanned or native) — not corrupted, encrypted, or password-protected.
- Sarvam AI account and API key will be available and funded (free tier) for the duration of the build.
- No confidential/classified document handling is required for this MVP demo set — sample documents used for testing should be non-sensitive or public where possible.

## 11. User Stories (for reference during build)
- *As an official*, I want to open a folder and see a plain-language summary next to each order, so I don't have to read the whole document to understand it.
- *As an official*, I want to ask "what orders were issued about X in the last quarter" and get an answer with references, so I can trust and verify it.
- *As an official*, I want to ask a question about one specific document I already have open, and get an answer that doesn't mix in unrelated documents.
- *As a mentor scientist*, I want to see a clear architecture and cost analysis, so I can evaluate whether this approach is worth scaling to production.
