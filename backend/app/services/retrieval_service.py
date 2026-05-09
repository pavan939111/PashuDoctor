import chromadb
import numpy as np
import os
import json
import pickle
import time
from rank_bm25 import BM25Okapi
from typing import List, Dict, Any, Optional
from app.config import get_settings

settings = get_settings()

class ChromaDBManager:
    def __init__(self):
        # 1. Initialize persistent client
        self.client = chromadb.PersistentClient(path=settings.CHROMA_PATH)
        
        # 2. Get or create collections
        self.disease_collection = self.client.get_or_create_collection(
            name="livestock_diseases",
            metadata={"hnsw:space": "cosine"}
        )
        
        self.knowledge_collection = self.client.get_or_create_collection(
            name="knowledge_base",
            metadata={"hnsw:space": "cosine"}
        )
        
        self.cases_collection = self.client.get_or_create_collection(
            name="resolved_cases",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Print stats
        d_count = self.disease_collection.count()
        k_count = self.knowledge_collection.count()
        
        print(f"ChromaDB Manager Initialized")
        print(f"Disease collection: {d_count} records")
        print(f"Knowledge collection: {k_count} records")

    def add_disease_image(
        self,
        image_id: str,
        embedding: np.ndarray,
        metadata: Dict[str, Any]
    ):
        """
        metadata must contain: animal, disease, body_part, severity, source, split
        """
        # Ensure embedding is a list
        emb_list = embedding.tolist() if isinstance(embedding, np.ndarray) else list(embedding)
        
        self.disease_collection.add(
            ids=[image_id],
            embeddings=[emb_list],
            metadatas=[metadata]
        )

    def add_knowledge_chunk(
        self,
        chunk_id: str,
        embedding: np.ndarray,
        metadata: Dict[str, Any],
        text: str
    ):
        """
        metadata must contain: source, disease_tags, animal_tags
        """
        emb_list = embedding.tolist() if isinstance(embedding, np.ndarray) else list(embedding)
        
        self.knowledge_collection.add(
            ids=[chunk_id],
            embeddings=[emb_list],
            metadatas=[metadata],
            documents=[text]
        )

    def query_diseases(
        self,
        query_embedding: np.ndarray,
        animal_type: str,
        body_part: Optional[str] = None,
        severity: Optional[str] = None,
        n_results: int = 20
    ) -> List[Dict[str, Any]]:
        
        emb_list = query_embedding.tolist() if isinstance(query_embedding, np.ndarray) else list(query_embedding)
        
        # Build complex filter
        where_filter = {"animal": animal_type}
        
        conditions = []
        if animal_type:
            conditions.append({"animal": animal_type})
        if body_part:
            conditions.append({"body_part": body_part})
        if severity:
            conditions.append({"severity": severity})
            
        if len(conditions) > 1:
            where_filter = {"$and": conditions}
        elif len(conditions) == 1:
            where_filter = conditions[0]
        else:
            where_filter = None

        results = self.disease_collection.query(
            query_embeddings=[emb_list],
            n_results=n_results,
            where=where_filter
        )
        
        # FALLBACK: If strict filtering returns too few results, try without body_part/severity
        if (not results["ids"] or not results["ids"][0] or len(results["ids"][0]) < 2) and (body_part or severity):
            fallback_filter = {"animal": animal_type} if animal_type else None
            results = self.disease_collection.query(
                query_embeddings=[emb_list],
                n_results=n_results,
                where=fallback_filter
            )
        
        # Format results
        formatted = []
        if results["ids"] and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                formatted.append({
                    "id": results["ids"][0][i],
                    "distance": results["distances"][0][i] if results["distances"] else 0,
                    "metadata": results["metadatas"][0][i]
                })
        return formatted

    def query_verified_cases(
        self,
        query_embedding: np.ndarray,
        animal_type: str,
        n_results: int = 10
    ) -> List[Dict[str, Any]]:
        """Queries the verified cases collection populated by farmer feedback"""
        emb_list = query_embedding.tolist() if isinstance(query_embedding, np.ndarray) else list(query_embedding)
        
        results = self.cases_collection.query(
            query_embeddings=[emb_list],
            n_results=n_results,
            where={"animal": animal_type}
        )
        
        formatted = []
        if results["ids"] and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                formatted.append({
                    "id": results["ids"][0][i],
                    "distance": results["distances"][0][i] if results["distances"] else 0,
                    "metadata": results["metadatas"][0][i]
                })
        return formatted

    def query_knowledge(
        self,
        query_embedding: np.ndarray,
        animal_type: Optional[str] = None,
        disease_hint: Optional[str] = None,
        n_results: int = 10
    ) -> List[Dict[str, Any]]:
        
        emb_list = query_embedding.tolist() if isinstance(query_embedding, np.ndarray) else list(query_embedding)
        
        conditions = []
        if animal_type:
            conditions.append({"animal_tags": {"$contains": animal_type}})
        if disease_hint:
            conditions.append({"disease_tags": {"$contains": disease_hint}})
            
        where_filter = None
        if len(conditions) > 1:
            where_filter = {"$and": conditions}
        elif len(conditions) == 1:
            where_filter = conditions[0]
            
        try:
            results = self.knowledge_collection.query(
                query_embeddings=[emb_list],
                n_results=n_results,
                where=where_filter
            )
            # Fallback logic if no results with specific filters
            if not results["ids"] or not results["ids"][0]:
                results = self.knowledge_collection.query(
                    query_embeddings=[emb_list],
                    n_results=n_results
                )
        except Exception as e:
            results = self.knowledge_collection.query(
                query_embeddings=[emb_list],
                n_results=n_results
            )
            
        formatted = []
        if results["ids"] and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                formatted.append({
                    "id": results["ids"][0][i],
                    "distance": results["distances"][0][i] if results["distances"] else 0,
                    "metadata": results["metadatas"][0][i],
                    "text": results["documents"][0][i] if results["documents"] else ""
                })
        return formatted

    def get_collection_stats(self) -> Dict[str, Any]:
        # Iterate all metadata to aggregate
        # NOTE: This can be slow for very large collections, but fine for our scale
        all_data = self.disease_collection.get(include=["metadatas"])
        metadatas = all_data["metadatas"]
        
        stats = {
            "total": len(metadatas),
            "by_animal": {},
            "by_disease": {}
        }
        
        for meta in metadatas:
            animal = meta.get("animal", "unknown")
            disease = meta.get("disease", "unknown")
            
            stats["by_animal"][animal] = stats["by_animal"].get(animal, 0) + 1
            stats["by_disease"][disease] = stats["by_disease"].get(disease, 0) + 1
            
        return stats

    def delete_and_rebuild(self, confirmation: str):
        if confirmation != "REBUILD":
            print("Action cancelled. Rebuild requires 'REBUILD' confirmation.")
            return
            
        try:
            self.client.delete_collection("livestock_diseases")
        except:
            pass
            
        try:
            self.client.delete_collection("knowledge_base")
        except:
            pass
            
        self.disease_collection = self.client.get_or_create_collection(
            name="livestock_diseases",
            metadata={"hnsw:space": "cosine"}
        )
        self.knowledge_collection = self.client.get_or_create_collection(
            name="knowledge_base",
            metadata={"hnsw:space": "cosine"}
        )
        print("Both collections deleted and recreated successfully.")

class BM25IndexManager:
    def __init__(self, chroma_manager: Optional[ChromaDBManager] = None):
        self.chroma = chroma_manager
        self.knowledge_path = os.path.join("data", "processed", "knowledge_bm25.pkl")
        self.symptom_path = os.path.join("data", "processed", "symptom_bm25.pkl")
        
        self.knowledge_docs = []
        self.symptom_docs = []
        
        self.knowledge_bm25 = None
        self.symptom_bm25 = None
        
        # Load or rebuild
        self.load_indexes()

    def _tokenize(self, text: str) -> List[str]:
        return text.lower().split()

    def load_indexes(self):
        if os.path.exists(self.knowledge_path) and os.path.exists(self.symptom_path):
            try:
                with open(self.knowledge_path, "rb") as f:
                    data = pickle.load(f)
                    self.knowledge_bm25 = data["bm25"]
                    self.knowledge_docs = data["docs"]
                
                with open(self.symptom_path, "rb") as f:
                    data = pickle.load(f)
                    self.symptom_bm25 = data["bm25"]
                    self.symptom_docs = data["docs"]
                
                print(f"BM25 indexes loaded: knowledge={len(self.knowledge_docs)} docs, symptom={len(self.symptom_docs)} docs")
                return
            except Exception as e:
                print(f"Error loading BM25 indexes: {e}. Rebuilding...")
        
        # If not loaded, rebuild if we have chroma manager
        if self.chroma:
            self.rebuild_indexes()
        else:
            print("BM25 indexes not found and no ChromaDBManager provided to rebuild.")

    def rebuild_indexes(self):
        print("Building BM25 indexes from scratch...")
        
        # 1. Load Knowledge Chunks
        chunks_path = os.path.join("data", "knowledge_base", "chunks.jsonl")
        self.knowledge_docs = []
        if os.path.exists(chunks_path):
            with open(chunks_path, "r", encoding="utf-8") as f:
                for line in f:
                    self.knowledge_docs.append(json.loads(line))
        
        tokenized_k_docs = [self._tokenize(doc["text"]) for doc in self.knowledge_docs]
        if tokenized_k_docs:
            self.knowledge_bm25 = BM25Okapi(tokenized_k_docs)
            with open(self.knowledge_path, "wb") as f:
                pickle.dump({"bm25": self.knowledge_bm25, "docs": self.knowledge_docs}, f)
        
        # 2. Load Disease Metadata from Chroma
        self.symptom_docs = []
        if self.chroma:
            all_data = self.chroma.disease_collection.get(include=["metadatas"])
            self.symptom_docs = [{"id": id_val, "metadata": meta} for id_val, meta in zip(all_data["ids"], all_data["metadatas"])]
            
            symptom_texts = []
            for doc in self.symptom_docs:
                m = doc["metadata"]
                # Use description if available, else fallback to basic tags
                text = m.get("description")
                if not text:
                    text = f"{m.get('animal', '')} {m.get('disease', '')} {m.get('body_part', '')} {m.get('severity', '')}"
                symptom_texts.append(text)
            
            tokenized_s_docs = [self._tokenize(text) for text in symptom_texts]
            if tokenized_s_docs:
                self.symptom_bm25 = BM25Okapi(tokenized_s_docs)
                with open(self.symptom_path, "wb") as f:
                    pickle.dump({"bm25": self.symptom_bm25, "docs": self.symptom_docs}, f)
        
        print(f"BM25 indexes built: knowledge={len(self.knowledge_docs)} docs, symptom={len(self.symptom_docs)} docs")

    def search_knowledge_bm25(self, query: str, top_k: int = 20) -> List[Dict[str, Any]]:
        if not self.knowledge_bm25:
            return []
        
        tokens = self._tokenize(query)
        scores = self.knowledge_bm25.get_scores(tokens)
        
        # Get top indices
        top_n = np.argsort(scores)[::-1][:top_k]
        
        results = []
        for idx in top_n:
            if scores[idx] < 0.01:
                continue
            doc = self.knowledge_docs[idx]
            results.append({
                "chunk_id": doc["chunk_id"],
                "text": doc["text"],
                "bm25_score": float(scores[idx]),
                "metadata": {
                    "source": doc.get("source"),
                    "disease_tags": doc.get("disease_tags"),
                    "animal_tags": doc.get("animal_tags")
                }
            })
        return results

    def search_symptom_bm25(self, query: str, animal_type: str = None, top_k: int = 20) -> List[Dict[str, Any]]:
        if not self.symptom_bm25:
            return []
        
        tokens = self._tokenize(query)
        scores = self.symptom_bm25.get_scores(tokens)
        
        # Get all results and filter by animal if provided
        all_indices = np.argsort(scores)[::-1]
        
        results = []
        for idx in all_indices:
            if scores[idx] < 0.01:
                continue
            
            doc = self.symptom_docs[idx]
            # Filter by animal
            if animal_type and doc["metadata"].get("animal") != animal_type:
                continue
                
            results.append({
                "image_id": doc["id"],
                "bm25_score": float(scores[idx]),
                "metadata": doc["metadata"]
            })
            
            if len(results) >= top_k:
                break
                
        return results

    def update_indexes_incremental(self, new_chunks: List[Dict[str, Any]]):
        # This is simplified - we just append and full rebuild for now
        self.knowledge_docs.extend(new_chunks)
        self.rebuild_indexes()

class HybridRetrievalEngine:
    def __init__(
        self, 
        chroma_manager: ChromaDBManager, 
        bm25_manager: BM25IndexManager,
        image_service: Any,
        text_service: Any
    ):
        self.chroma = chroma_manager
        self.bm25 = bm25_manager
        self.image_service = image_service
        self.text_service = text_service
        
        self.dense_weight = settings.DENSE_WEIGHT
        self.bm25_weight = settings.BM25_WEIGHT
        
        print("HybridRetrievalEngine initialised")

    def normalize_scores(self, scores: List[float]) -> List[float]:
        if not scores:
            return []
        s_min = min(scores)
        s_max = max(scores)
        if s_max == s_min:
            return [1.0 if s_max > 0 else 0.0] * len(scores)
        return [(s - s_min) / (s_max - s_min) for s in scores]

    def retrieve_disease_candidates(
        self,
        image_embedding: np.ndarray,
        symptom_text: str,
        animal_type: str,
        top_k: int = 20
    ) -> List[Dict[str, Any]]:
        
        # 1. Dense Retrieval (Similarity = 1 - Distance)
        dense_results = self.chroma.query_diseases(image_embedding, animal_type, n_results=top_k * 2)
        
        # 2. Verified Case Retrieval (Learning Loop)
        # We use symptom embedding for dense lookup of historical cases if available
        # Note: image_embedding here is CLIP, but cases_collection might use text embeddings
        # For the loop to work, we should use the appropriate embedding.
        # However, retrieve_all currently passes image_embedding (CLIP) to this method.
        # If cases were stored with symptom embeddings, we should query with symptom_emb.
        
        # Let's check verified cases as well
        verified_results = self.chroma.query_verified_cases(image_embedding, animal_type, n_results=top_k)

        # 3. BM25 Retrieval
        bm25_results = self.bm25.search_symptom_bm25(symptom_text, animal_type=animal_type, top_k=top_k * 2)
        
        # 4. Score Fusion
        candidates = {}
        
        for res in dense_results:
            idx = res["id"]
            candidates[idx] = {
                "dense_score": 1.0 - res["distance"],
                "bm25_score": 0.0,
                "metadata": res["metadata"]
            }
            
        for res in bm25_results:
            idx = res["image_id"]
            if idx in candidates:
                candidates[idx]["bm25_score"] = res["bm25_score"]
            else:
                candidates[idx] = {
                    "dense_score": 0.0,
                    "bm25_score": res["bm25_score"],
                    "metadata": res["metadata"]
                }

        for res in verified_results:
            idx = res["id"]
            if idx in candidates:
                # Boost existing candidate if it also appears in verified cases
                candidates[idx]["dense_score"] = max(candidates[idx]["dense_score"], 1.0 - res["distance"])
                candidates[idx]["metadata"]["source"] = "verified_case" # Mark as high-trust
            else:
                candidates[idx] = {
                    "dense_score": 1.0 - res["distance"],
                    "bm25_score": 0.0,
                    "metadata": res["metadata"]
                }
                
        # 4. Normalize
        ids = list(candidates.keys())
        if not ids: return []
        
        dense_scores = [candidates[i]["dense_score"] for i in ids]
        bm25_scores = [candidates[i]["bm25_score"] for i in ids]
        
        norm_dense = self.normalize_scores(dense_scores)
        norm_bm25 = self.normalize_scores(bm25_scores)
        
        # 5. Combine and Sort
        final_list = []
        for i, idx in enumerate(ids):
            score = (self.dense_weight * norm_dense[i]) + (self.bm25_weight * norm_bm25[i])
            final_list.append({
                "image_id": idx,
                "final_score": float(score),
                "dense_score": float(dense_scores[i]),
                "bm25_score": float(bm25_scores[i]),
                "metadata": candidates[idx]["metadata"]
            })
            
        final_list.sort(key=lambda x: x["final_score"], reverse=True)
        return final_list[:top_k]

    def retrieve_knowledge_candidates(
        self,
        text_embedding: np.ndarray,
        symptom_text: str,
        disease_hint: str = None,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        
        # 1. Dense Retrieval
        dense_results = self.chroma.query_knowledge(text_embedding, disease_hint, n_results=top_k * 2)
        
        # 2. BM25 Retrieval
        bm25_results = self.bm25.search_knowledge_bm25(symptom_text, top_k=top_k * 2)
        
        # 3. Fusion
        candidates = {}
        for res in dense_results:
            idx = res["id"]
            candidates[idx] = {
                "dense_score": 1.0 - res["distance"],
                "bm25_score": 0.0,
                "text": res["text"],
                "metadata": res["metadata"]
            }
            
        for res in bm25_results:
            idx = res["chunk_id"]
            if idx in candidates:
                candidates[idx]["bm25_score"] = res["bm25_score"]
            else:
                candidates[idx] = {
                    "dense_score": 0.0,
                    "bm25_score": res["bm25_score"],
                    "text": res["text"],
                    "metadata": res["metadata"]
                }
                
        ids = list(candidates.keys())
        if not ids: return []
        
        norm_dense = self.normalize_scores([candidates[i]["dense_score"] for i in ids])
        norm_bm25 = self.normalize_scores([candidates[i]["bm25_score"] for i in ids])
        
        final_list = []
        for i, idx in enumerate(ids):
            score = (self.dense_weight * norm_dense[i]) + (self.bm25_weight * norm_bm25[i])
            final_list.append({
                "chunk_id": idx,
                "final_score": float(score),
                "dense_score": float(candidates[idx]["dense_score"]),
                "bm25_score": float(candidates[idx]["bm25_score"]),
                "text": candidates[idx]["text"],
                "metadata": candidates[idx]["metadata"]
            })
            
        final_list.sort(key=lambda x: x["final_score"], reverse=True)
        return final_list[:top_k]

    async def retrieve_all(
        self,
        image_path: str | List[str],
        symptom_text: str,
        animal_type: str = None
    ) -> Dict[str, Any]:
        
        start_time = time.time()
        
        # 1. Metadata Extraction (LLM-driven identifying animal/symptoms/severity)
        # We assume llm_service is available via a dependency or passed in. 
        # For efficiency, we use the text_service for basic metadata or assume it's passed.
        # But here we'll use a fast heuristic or the llm if we can.
        
        # 2. Animal Detection & Embedding
        animal_conf = 1.0
        if isinstance(image_path, list):
            if not animal_type and image_path:
                detection = self.image_service.detect_animal(image_path[0])
                animal_type = detection["animal"]
                animal_conf = detection["confidence"]
            image_emb = self.image_service.get_combined_embedding(image_path)
        else:
            if not animal_type and image_path:
                detection = self.image_service.detect_animal(image_path)
                animal_type = detection["animal"]
                animal_conf = detection["confidence"]
            image_emb = self.image_service.get_image_embedding(image_path) if image_path else np.zeros(512)
        
        # 3. Text Embedding
        text_emb_384 = self.text_service.get_text_embedding(symptom_text)
        
        # 4. Retrieve Disease Candidates
        # We start with a broader search to avoid strict filter misses
        disease_candidates = self.retrieve_disease_candidates(
            image_embedding=image_emb,
            symptom_text=symptom_text,
            animal_type=animal_type,
            top_k=20
        )
        
        # 4.1 Apply Soft Metadata Filtering (Boost matches)
        body_part_hint = None
        severity_hint = None
        for part in ["udder", "hoof", "mouth", "eye", "skin", "leg", "ear"]:
            if part in symptom_text.lower():
                body_part_hint = part
                break
                
        if body_part_hint:
            # Boost candidates that match the body part
            for cand in disease_candidates:
                if cand.get("metadata", {}).get("body_part") == body_part_hint:
                    cand["final_score"] = min(1.0, cand["final_score"] * 1.2)
            # Re-sort
            disease_candidates.sort(key=lambda x: x["final_score"], reverse=True)
        
        # 5. Retrieve Knowledge Chunks
        disease_hint = None
        if disease_candidates and (disease_candidates[0].get("final_score", 0) > 0.5 or disease_candidates[0].get("distance", 1) < 0.4):
            # In query_diseases result, it might be 'metadata'
            disease_hint = disease_candidates[0].get("metadata", {}).get("disease")
            
        knowledge_chunks = self.retrieve_knowledge_candidates(
            text_emb_384,
            symptom_text=symptom_text,
            disease_hint=disease_hint,
            top_k=10
        )
        
        end_time = time.time()
        
        return {
            "animal_type": animal_type,
            "animal_confidence": float(animal_conf),
            "metadata": {
                "body_part": body_part_hint,
                "severity": severity_hint
            },
            "disease_candidates": disease_candidates,
            "knowledge_chunks": knowledge_chunks,
            "retrieval_time_ms": (end_time - start_time) * 1000
        }
