# PashuDoctor — Full Implementation Report

## 1. Project Identity
- **Project Name**: PashuDoctor
- **Version**: 1.0.0
- **Description**: A multi-modal, offline-resilient AI diagnostic assistant for Indian livestock farmers, supporting cattle, buffalo, goat, and sheep.
- **Target Users**: Rural livestock farmers in India with limited internet connectivity and literacy barriers.
- **Problem Solved**:
    - Lack of immediate access to veterinary expertise in remote areas.
    - High economic loss due to delayed diagnosis of contagious diseases like FMD and LSD.
    - Communication barriers between farmers and vets due to technical and linguistic gaps.
- **Core Innovation**: Hybrid RAG architecture combining CLIP-based visual retrieval, BM25 text retrieval, and a closed-loop active learning system using farmer feedback.

## 2. Technical Architecture
- **Diagnostic Engine**:
    - **Multi-modal Retrieval**: CLIP (ViT-B/32) for image embeddings and Sentence-Transformers (all-MiniLM-L6-v2) for text.
    - **Hybrid Search**: Fused retrieval from ChromaDB (Dense) and BM25 (Sparse) with weighted scoring (Dense: 0.3, BM25: 0.7).
    - **Reranking**: BAAI/bge-reranker-base for precise candidate filtering.
    - **LLM Reasoning**: Google Gemini 1.5 Flash for diagnosis synthesis, precautions, and farmer advice.
- **Offline Resilience**:
    - **Speech-to-Text**: Local OpenAI Whisper (small) model for offline transcription.
    - **Translation**: ArgosTranslate for local multilingual support.
    - **Offline Triage**: Connectivity-aware detector (`is_online()`) that switches to local caching and emergency fast-path keywords when disconnected.
- **Active Learning Loop**:
    - **Feedback Integration**: Verified correct cases are re-embedded and stored in a specialized `resolved_cases` collection in ChromaDB.
    - **Self-Improvement**: Future retrievals prioritize these verified cases, increasing system accuracy over time without manual updates.

## 3. Communication & Distribution
- **WhatsApp Integration**: Deep-linked sharing of diagnostic reports (Animal, Diagnosis, Confidence, Severity, Precautions) for one-tap vet consultation.
- **Multilingual Support**: UI and diagnostics available in 10 Indian languages (Hindi, Tamil, Telugu, Kannada, Malayalam, Marathi, Bengali, Punjabi, Gujarati, and English).
- **Voice-First UI**: Integrated speech recording and Text-to-Speech (gTTS) for accessibility.

## 4. Safety & Compliance
- **Emergency Protocols**: Sub-10ms keyword triage for life-threatening conditions.
- **Herd Biosecurity**: Automatic regional outbreak alerts based on a monthly-updated static database (`STATIC_ALERT_DB`).
- **Safety Disclaimers**: Non-prescriptive responses with mandatory veterinary consultation warnings on every report.

## 5. Deployment Specs
- **Backend**: FastAPI with SQLite (History) and ChromaDB (Vector Store).
- **Frontend**: Streamlit with custom glassmorphism styling and responsive layout.
- **Hardware**: CPU-optimized for local execution; GPU support for CLIP/Whisper where available.
