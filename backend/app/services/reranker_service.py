import time
import numpy as np
from sentence_transformers import CrossEncoder
from typing import List, Dict, Any

class RerankerService:
    def __init__(self):
        # 1. Load Model
        self.model = CrossEncoder("BAAI/bge-reranker-base")
        self.device = self.model.device
        print(f"RerankerService loaded: BAAI/bge-reranker-base on {self.device}")

    def _normalize_reranker_scores(self, scores: np.ndarray) -> np.ndarray:
        if len(scores) == 0:
            return scores
        s_min = scores.min()
        s_max = scores.max()
        if s_max == s_min:
            return np.ones_like(scores) if s_max > -10 else np.zeros_like(scores)
        return (scores - s_min) / (s_max - s_min)

    def rerank_disease_candidates(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        if not candidates:
            return []

        # Build query string
        query_str = f"livestock disease diagnosis: {query}"

        # Build document strings
        documents = []
        for c in candidates:
            m = c["metadata"]
            doc_str = f"{m.get('animal', 'unknown')} animal, disease: {m.get('disease', 'unknown')}, body part: {m.get('body_part', 'unknown')}, severity: {m.get('severity', 'unknown')}"
            documents.append(doc_str)

        # Create pairs
        pairs = [(query_str, doc) for doc in documents]

        # Get reranker scores
        reranker_scores = self.model.predict(pairs)
        norm_reranker = self._normalize_reranker_scores(reranker_scores)

        # Compute combined score: 0.4 * reranker + 0.6 * retrieval
        for i, candidate in enumerate(candidates):
            candidate["reranker_score"] = float(reranker_scores[i])
            candidate["combined_score"] = (0.4 * float(norm_reranker[i])) + (0.6 * candidate["final_score"])

        # Sort by combined score
        candidates.sort(key=lambda x: x["combined_score"], reverse=True)
        return candidates[:top_k]

    def rerank_knowledge_chunks(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        if not chunks:
            return []

        # Build pairs
        pairs = [(query, chunk["text"]) for chunk in chunks]

        # Get reranker scores
        reranker_scores = self.model.predict(pairs)
        norm_reranker = self._normalize_reranker_scores(reranker_scores)

        # Add scores and sort
        for i, chunk in enumerate(chunks):
            chunk["reranker_score"] = float(reranker_scores[i])
            # For knowledge, we might want a different mix, but let's stick to simple sort or same mix
            chunk["combined_score"] = (0.4 * float(norm_reranker[i])) + (0.6 * chunk["final_score"])

        chunks.sort(key=lambda x: x["combined_score"], reverse=True)
        return chunks[:top_k]

    def rerank_all(
        self,
        symptom_query: str,
        retrieval_results: Dict[str, Any],
        top_k_disease: int = 3,
        top_k_knowledge: int = 5
    ) -> Dict[str, Any]:
        
        start_time = time.time()
        
        # Rerank Disease Candidates
        if "disease_candidates" in retrieval_results:
            retrieval_results["disease_candidates"] = self.rerank_disease_candidates(
                symptom_query, 
                retrieval_results["disease_candidates"], 
                top_k=top_k_disease
            )
            
        # Rerank Knowledge Chunks
        if "knowledge_chunks" in retrieval_results:
            retrieval_results["knowledge_chunks"] = self.rerank_knowledge_chunks(
                symptom_query, 
                retrieval_results["knowledge_chunks"], 
                top_k=top_k_knowledge
            )
            
        end_time = time.time()
        retrieval_results["reranking_time_ms"] = (end_time - start_time) * 1000
        
        return retrieval_results

    def get_top_disease(self, reranked_candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not reranked_candidates:
            return {}
        
        top = reranked_candidates[0]
        m = top["metadata"]
        
        return {
            "disease": m.get("disease", "unknown"),
            "animal": m.get("animal", "unknown"),
            "confidence": top.get("combined_score", 0.0),
            "body_part": m.get("body_part", "unknown"),
            "severity": m.get("severity", "unknown")
        }
