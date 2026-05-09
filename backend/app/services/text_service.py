import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
from functools import lru_cache
from typing import List, Dict, Any

class TextEmbeddingService:
    def __init__(self):
        # 1. Load Model
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.dim = 384
        
        self.DISEASE_SYMPTOM_MAP = {
            "foot_and_mouth": "blisters on mouth hooves teats fever drooling lameness reduced milk",
            "mastitis": "swollen udder hot painful udder abnormal milk clots pus reduced milk yield fever",
            "lumpy_skin_disease": "skin nodules lumps fever enlarged lymph nodes nasal discharge weight loss",
            "blackquarter": "sudden death muscle swelling lameness fever crackling sound in muscle gas gangrene",
            "hemorrhagic_septicemia": "high fever swelling throat neck difficulty breathing sudden death monsoon season",
            "ppr": "fever oral lesions diarrhoea nasal discharge pneumonia goats sheep only",
            "healthy": "healthy normal animal no visible disease signs good body condition"
        }
        
        print("TextEmbeddingService loaded")

    @lru_cache(maxsize=512)
    def get_text_embedding(self, text: str) -> np.ndarray:
        if not text:
            return np.zeros(self.dim)
        
        # Encode and normalize
        embedding = self.model.encode(text)
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        return embedding

    def get_disease_text(self, disease: str, animal: str) -> str:
        symptoms = self.DISEASE_SYMPTOM_MAP.get(disease, "unknown symptoms")
        
        # Mapping specific body parts or details based on disease for "richer" description
        body_parts = {
            "foot_and_mouth": "mouth and hooves",
            "mastitis": "udder",
            "lumpy_skin_disease": "skin",
            "blackquarter": "muscles",
            "hemorrhagic_septicemia": "throat and neck",
            "ppr": "respiratory and digestive systems",
            "healthy": "entire body"
        }
        
        part = body_parts.get(disease, "body")
        
        return (
            f"{animal} with {disease}. Symptoms include {symptoms}. "
            f"Common in Indian livestock. Affects {part}."
        )

    def embed_knowledge_chunk(self, chunk: dict) -> np.ndarray:
        # Combine text with tags
        disease_tags = ", ".join(chunk.get("disease_tags", []))
        animal_tags = ", ".join(chunk.get("animal_tags", []))
        
        combined_text = f"Context: {chunk.get('text', '')}\nTags: {disease_tags}, {animal_tags}"
        return self.get_text_embedding(combined_text)

    def batch_embed_texts(self, texts: list, batch_size=64) -> list:
        embeddings = []
        for i in tqdm(range(0, len(texts), batch_size), desc="Text Embedding"):
            batch = texts[i:i+batch_size]
            batch_embs = self.model.encode(batch)
            # Normalize batch
            norms = np.linalg.norm(batch_embs, axis=1, keepdims=True)
            batch_embs = np.divide(batch_embs, norms, out=np.zeros_like(batch_embs), where=norms!=0)
            embeddings.extend(batch_embs)
        return embeddings
