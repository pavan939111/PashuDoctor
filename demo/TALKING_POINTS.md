# PashuDoctor Technical Talking Points 🎤

## 1. Multi-Modal RAG (The "Secret Sauce")
- **Hybrid Search**: We don't just use embeddings. We combine CLIP image similarity with BM25 keyword matching. This ensures that even if an image is blurry, the symptom description pulls the right knowledge.
- **Reranking Layer**: Using a BGE Cross-Encoder ensures that the top 3 candidates are technically the most relevant, not just the nearest neighbors.

## 2. Gemini-Only Architecture
- **Vision + Reasoning**: We use Gemini 1.5 Flash for both image analysis (when CLIP is uncertain) and the final diagnostic reasoning.
- **Key Rotation**: Production-ready handling of API quotas. We automatically rotate keys on 429 errors, ensuring the demo never hangs.

## 3. Performance & Optimization
- **Low Latency**: End-to-end retrieval and reranking in < 20ms on CPU.
- **Efficiency**: CLIP and Small-MiniLM embeddings allow us to run the heavy retrieval part on standard hardware without expensive GPUs.
- **Concurrency**: FastAPI with `anyio` thread-pooling ensures the UI stays responsive even during heavy AI inference.

## 4. Grounding & Safety
- **Knowledge-Grounded**: Every diagnosis is backed by retrieved veterinary knowledge.
- **Confidence Scoring**: If the system isn't sure, it asks follow-up questions instead of guessing.
- **Farmer-Centric**: Responses are automatically formatted for non-expert readability while maintaining clinical depth for veterinarians.
