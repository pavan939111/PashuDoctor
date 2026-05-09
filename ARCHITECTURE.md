# PashuDoctor — Full System Architecture

## 1. System Overview Diagram (ASCII)

┌─────────────────────────────────────────────┐
│              FARMER (User)                  │
│     Image │ Voice │ Text │ Language Selector│
└───────────────────┬─────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│             FRONTEND (Next.js 15)           │
│  UI Components │ Tailwind 4.0 │ Lucide Icons│
└───────────────────┬─────────────────────────┘
                    ↓ (REST API / WebSocket)
┌─────────────────────────────────────────────┐
│             BACKEND (FastAPI)               │
│   Routers (Analyze, Chat, History, Alerts)  │
│   Middleware (CORS, Limiter, Logging)       │
└───────────────────┬─────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│             SERVICE LAYER (AI)              │
│ ┌──────────────┐ ┌──────────────┐ ┌───────┐ │
│ │ Image (CLIP) │ │ Retrieval    │ │ Rerank│ │
│ └──────────────┘ └──────────────┘ └───────┘ │
│ ┌──────────────┐ ┌──────────────┐ ┌───────┐ │
│ │ LLM (Gemini) │ │ Memory (SQL) │ │ Utils │ │
│ └──────────────┘ └──────────────┘ └───────┘ │
└───────────────────┬─────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│               DATA LAYER                    │
│ ┌──────────────┐ ┌──────────────┐ ┌───────┐ │
│ │ ChromaDB     │ │ SQLite       │ │ Files │ │
│ │ (Vectors)    │ │ (History)    │ │ (Logs)│ │
└───────────────────┴─────────────────────────┘

## 2. Component Architecture

### 2.1 Frontend Layer
frontend_next/
├── app/                      # Next.js App Router (Page, Layouts, Globals).
├── components/
│   ├── ChatInterface.tsx     # Provides the multi-turn conversational AI interface.
│   ├── Sidebar.tsx           # Manages the display and management of past case records.
│   ├── AnalysisReport.tsx    # Visualizes structured clinical reports and confidence scores.
│   └── ImageUpload.tsx       # Handles multimodal image ingestion and previews.
├── lib/
│   ├── utils.ts              # Shared utility functions and Tailwind merging.
│   └── api.ts                # Client-side API orchestration for FastAPI communication.
└── types/
    └── index.ts              # TypeScript definitions for Cases, Messages, and AI Responses.

### 2.2 Backend Layer
backend/app/
├── main.py                  # FastAPI application initialization and middleware setup.
├── config.py                # Pydantic-based settings and environment variable management.
├── dependencies.py          # Service registry and dependency injection singletons.
├── models/
│   ├── schemas.py           # Pydantic models for request/response data validation.
│   ├── case.py              # SQLAlchemy ORM models for case and chat history.
│   └── user.py              # SQLAlchemy model for farmer profile management.
├── routers/
│   ├── analyze.py           # Endpoints for multi-modal and text-only diagnostic analysis.
│   ├── chat.py              # Manages conversational logic and streaming AI messages.
│   └── history.py           # Handles case history retrieval, statistics, and feedback.
├── services/
│   ├── image_service.py     # CLIP-based feature extraction and species detection.
│   ├── retrieval_service.py # Orchestrates hybrid search and vector database logic.
│   ├── reranker_service.py  # Cross-Encoder refinement of diagnostic candidates.
│   ├── llm_service.py       # Gemini API orchestration with automated key rotation.
│   └── memory_service.py    # Synchronizes case data between SQLite and ChromaDB.
└── utils/
    ├── confidence.py        # Implements multi-factor diagnostic scoring and triage.
    ├── prompts.py           # Central repository for all LLM instruction templates.
    ├── breed_intelligence.py # Breed-specific risk assessments and clinical context.
    ├── herd_alert.py        # Detection and advisory for contagious livestock diseases.
    └── connectivity.py      # Autonomous internet status detection for offline fallbacks.

### 2.3 Data Layer
data/
├── raw/                     # Source dataset images from Kaggle and Roboflow.
├── processed/
│   ├── master_manifest.csv  # Global registry of all images with metadata.
│   ├── clean_manifest.csv   # Post-validation dataset ready for embedding.
│   ├── removed_manifest.csv # Log of images rejected during cleaning.
│   └── *.pkl               # Serialized BM25 index and IDF metadata.
├── knowledge_base/
│   ├── pdfs/               # Veterinary manuals from FAO, ICAR, and NGOs.
│   ├── texts/              # Raw text extracted from manual PDFs.
│   ├── chunks.jsonl        # Overlapping text chunks for granular retrieval.
│   └── disease_descriptions.json # Structured definitions of supported diseases.
├── chroma_db/              # Persistent vector storage for embeddings.
├── uploads/                # Runtime storage for farmer-submitted diagnostic images.
└── evaluation/             # Metrics, confusion matrices, and accuracy reports.

## 3. Request Lifecycle — Full Detail

### 3.1 Standard Diagnosis Request
1. Farmer uploads images and types symptoms. (0ms)
2. Frontend translates symptoms to English via `LanguageService`. (~200ms)
3. Frontend sends `multipart/form-data` to `/analyze/image`. (~100ms)
4. API checks for Emergency Keywords. (<5ms)
5. API saves images to `data/uploads/`. (~20ms)
6. `ImageService` runs quality check and species detection via CLIP. (~150ms)
7. `ImageService` extracts visual embeddings (512d). (~200ms)
8. `TextService` extracts symptom embeddings (512d). (~100ms)
9. `RetrievalService` performs Dense Search in ChromaDB. (~50ms)
10. `RetrievalService` performs Sparse Search via BM25. (~30ms)
11. `HybridRetrieval` fuses scores using 0.5/0.5 weighting. (~10ms)
12. `RerankerService` scores top 20 candidates via Cross-Encoder. (~400ms)
13. `ConfidenceUtils` computes multi-factor score (Image + Text + Symptoms). (~5ms)
14. `LLMRouter` selects Gemini model based on confidence. (~10ms)
15. `LLMService` sends prompt + images to Gemini 1.5 Flash. (~1200ms)
16. `HerdAlert` checks if primary diagnosis is contagious. (<5ms)
17. `MemoryService` saves record to SQLite. (~15ms)
18. API returns `AnalyzeResponse` JSON. (~10ms)
19. Frontend receives JSON and translates to target language. (~300ms)
20. Farmer sees full diagnosis with confidence and precautions. (Total: ~3s)

### 3.2 Emergency Fast-Path Request
1. User types "My cow is collapsed and dying".
2. `check_emergency()` in `analyze.py` triggers on "collapsed" and "dying".
3. System bypasses all RAG and LLM logic.
4. Returns predefined `EMERGENCY DETECTED` response with 1962 helpline.
5. Latency: **<10ms** total.

### 3.3 Offline Mode Request
1. `is_online()` returns `False`.
2. `SpeechService` swaps Google Cloud STT for **Local Whisper**.
3. `LanguageService` swaps Google Translate for **Local ArgosTranslate**.
4. `LLMRouter` detects offline status and looks up **DIAGNOSIS_CACHE**.
5. If found, returns cached response. If not, returns "Offline - Limited" warning.

### 3.4 Multi-turn Chat Request
1. User sends message in Chat tab.
2. `MemoryService` retrieves last 10 messages and case context.
3. Symptoms are enriched with new chat info and RAG is re-run.
4. LLM receives history + new RAG context + system prompt.
5. Response is streamed back to user via WebSocket.

## 4. Database Schema

### 4.1 SQLite Tables
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR NOT NULL,
    phone VARCHAR UNIQUE,
    region VARCHAR,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE cases (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR INDEX,
    animal_type VARCHAR,
    symptoms_text TEXT,
    image_path TEXT,
    primary_diagnosis VARCHAR,
    alternative_diagnoses JSON,
    matching_symptoms JSON,
    confidence_score FLOAT,
    severity VARCHAR,
    vet_urgency VARCHAR,
    feedback_correct BOOLEAN,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE chat_messages (
    id VARCHAR(36) PRIMARY KEY,
    case_id VARCHAR REFERENCES cases(id),
    role VARCHAR, -- 'user', 'assistant'
    content TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 4.2 ChromaDB Collections
- **livestock_diseases**: 
  - Metric: Cosine | Dims: 512 | Records: ~5k
  - Metadata: {animal: str, disease: str, severity: str}
- **knowledge_base**: 
  - Metric: Cosine | Dims: 512 | Records: ~1.2k
  - Metadata: {source: str, disease_tags: str}
- **resolved_cases**: 
  - Metric: Cosine | Dims: 512 | Records: Dynamic
  - Metadata: {case_id: str, verified: bool}

### 4.3 LRU Cache Structure
- **Key**: `f"{animal_type}_{symptoms_text[:50]}"`
- **Value**: Full `AnalyzeResponse` JSON.
- **Eviction**: Least Recently Used (LRU) with 50-item limit.

## 5. AI Pipeline Deep Dive

### 5.1 Embedding Strategy
- **Formula**: `combined = 0.6 * image_emb + 0.4 * text_emb`
- **Rationale**: Images (CLIP) provide direct visual evidence, while text embeddings provide clinical context. High weight for visual evidence ensures field deployment accuracy.

### 5.2 Hybrid Retrieval Formula
- **Formula**: `final_score = 0.3 * norm_dense + 0.7 * norm_bm25`
- **Normalization**: Min-Max normalization applied across candidates within each search mode.

### 5.3 Confidence Scoring Formula
- **Formula**: `score = 0.5*image_sim + 0.3*text_sim + 0.2*symptom_match`
- **Routing**:
  - <0.50: `ask_more` (No prediction shown)
  - 0.50 - 0.75: `show_options` (Possible conditions)
  - >0.75: `suggest` (High confidence)

### 5.4 Reranking Integration
- **Formula**: `final = 0.7 * retrieval_score + 0.3 * reranker_score`
- **K-Flow**: 40 candidates retrieved → 20 candidates reranked → Top 3 sent to LLM.

## 6. Speech & Language Architecture

### 6.1 Online Mode Pipeline
- Latency: ~1.5s total.
- Flow: Voice → Google API → Translation → LLM → Translation → gTTS → User.

### 6.2 Offline Mode Pipeline
- Latency: ~3.0s total (CPU bound).
- Flow: Voice → Whisper Local → ArgosTranslate → Cache Lookup → ArgosTranslate → User.

## 7. Safety Architecture

### 7.1 Emergency Keyword System
Keywords like "dying", "collapsed", "bleeding" in 10 languages trigger immediate helpline referral. Bypass logic is a simple string match before any AI services are invoked.

### 7.2 Confidence Gate System
Tiers: Emergency (Keywords) → Strong (Score > 0.9) → Suggest (Score > 0.75) → Ask More (Score < 0.5).

## 8. Performance Architecture
- **Async Thread Pool**: Used for CPU-bound tasks (CLIP inference, Reranking) to avoid blocking the FastAPI event loop.
- **Key Rotation**: Round-robin rotation across up to 10 Gemini keys. If a key fails 3 times, it is marked as "cooldown" for 60 minutes.

## 9. Deployment Architecture
- **Docker**: Single `docker-compose` with `backend`, `frontend`, and `ollama` (optional) services.
- **Volumes**: Persistent storage for `/data` (DBs) and `/logs`.

## 10. API Reference

### POST /analyze/image
**Description**: Primary multimodal diagnostic endpoint.
**Fields**: `user_id` (STR), `images` (FILES), `symptom_text` (STR), `animal_type` (STR), `language` (STR).
**Success Response**: `AnalyzeResponse` with `case_id` and `diagnosis`.
