import os
import json
import torch
import clip
import numpy as np
from PIL import Image
import google.generativeai as genai
from tqdm import tqdm
from functools import lru_cache
from typing import List, Dict, Any, Tuple
from app.config import get_settings

settings = get_settings()

def check_image_quality(image_path_or_file) -> dict:
    """Checks image quality (size and variance) without needing CLIP/LLM models"""
    try:
        from PIL import Image
        with Image.open(image_path_or_file) as img:
            # Check size
            width, height = img.size
            if width < 64 or height < 64:
                return {"valid": False, "reason": f"Image size too small ({width}x{height})"}
            
            # Check variance (avoid black/white images)
            img_np = np.array(img.convert("L"))
            std = np.std(img_np)
            if std < 10:
                return {"valid": False, "reason": f"Image lacks detail (low variance: {std:.2f})"}
            
            return {"valid": True, "reason": "OK"}
    except Exception as e:
        return {"valid": False, "reason": f"File error: {str(e)}"}

class ImageService:
    def __init__(self):
        # 1. Load CLIP
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model, self.preprocess = clip.load("ViT-B/32", device=self.device)
        
        # 2. Load Gemini with Round-Robin Support
        self.api_keys = settings.get_gemini_keys()
        self.current_key_idx = 0
        self._configure_gemini()
        
        self.ANIMAL_PROMPTS = [
            "a photo of a cow",
            "a photo of a buffalo",
            "a photo of a goat",
            "a photo of a sheep",
            "a photo of something else"
        ]
        
        print(f"ImageService loaded on {self.device}")
        if self.api_keys:
            print(f"Gemini Rotation enabled with {len(self.api_keys)} keys.")

    def _configure_gemini(self):
        if not self.api_keys:
            print("WARNING: No Gemini API keys found.")
            return
        key = self.api_keys[self.current_key_idx]
        genai.configure(api_key=key)
        self.gemini = genai.GenerativeModel("gemini-flash-latest")

    def rotate_key(self):
        if not self.api_keys:
            return
        self.current_key_idx = (self.current_key_idx + 1) % len(self.api_keys)
        self._configure_gemini()
        print(f"Rotated to Gemini Key #{self.current_key_idx + 1}")

    @lru_cache(maxsize=256)
    def get_image_embedding(self, image_path: str) -> np.ndarray:
        try:
            with Image.open(image_path) as img:
                image_input = self.preprocess(img.convert("RGB")).unsqueeze(0).to(self.device)
            
            with torch.no_grad():
                image_features = self.model.encode_image(image_input)
                # Normalize
                image_features /= image_features.norm(dim=-1, keepdim=True)
            
            return image_features.cpu().numpy().flatten()
        except Exception as e:
            print(f"Error getting embedding for {image_path}: {e}")
            return np.zeros(512)

    def get_combined_embedding(self, image_paths: list) -> np.ndarray:
        """Computes a mean normalized embedding from multiple images"""
        if not image_paths:
            return np.zeros(512)
            
        embeddings = [self.get_image_embedding(p) for p in image_paths]
        # Mean across embeddings
        combined = np.mean(embeddings, axis=0)
        # Re-normalize
        norm = np.linalg.norm(combined)
        if norm > 0:
            combined = combined / norm
        return combined

    @lru_cache(maxsize=128)
    def detect_animal_clip(self, image_path: str) -> dict:
        try:
            with Image.open(image_path) as img:
                image_input = self.preprocess(img.convert("RGB")).unsqueeze(0).to(self.device)
            text_tokens = clip.tokenize(self.ANIMAL_PROMPTS).to(self.device)
            
            with torch.no_grad():
                image_features = self.model.encode_image(image_input)
                text_features = self.model.encode_text(text_tokens)
                
                # Normalize
                image_features /= image_features.norm(dim=-1, keepdim=True)
                text_features /= text_features.norm(dim=-1, keepdim=True)
                
                # Similarity
                similarity = (100.0 * image_features @ text_features.T).softmax(dim=-1)
                values, indices = similarity[0].topk(1)
            
            probs = similarity[0].cpu().numpy()
            label_probs = {p.replace("a photo of a ", ""): float(prob) for p, prob in zip(self.ANIMAL_PROMPTS, probs)}
            
            best_label = self.ANIMAL_PROMPTS[indices[0]].replace("a photo of a ", "")
            
            return {
                "animal": best_label,
                "confidence": float(values[0]),
                "method": "clip",
                "all_probs": label_probs
            }
        except Exception as e:
            print(f"CLIP detection error: {e}")
            return {"animal": "unknown", "confidence": 0.0, "method": "clip", "all_probs": {}}

    def detect_animal_gemini(self, image_path: str, retries=None) -> dict:
        if retries is None:
            retries = len(self.api_keys)
        try:
            with Image.open(image_path) as img:
                prompt = (
                    "Identify the animal in this image. Reply ONLY with valid JSON: "
                    "{animal: cow/buffalo/goat/sheep/unknown, "
                    "confidence: 0.0-1.0, "
                    "reason: one sentence}"
                )
                
                try:
                    response = self.gemini.generate_content([prompt, img])
                except Exception as e:
                    err_msg = str(e)
                    retry_worthy = ["429", "ResourceExhausted", "401", "Unauthorized", "403", "PermissionDenied", "invalid api key", "400"]
                    
                    if any(term.lower() in err_msg.lower() for term in retry_worthy) and retries > 0:
                        print(f"Gemini Detection error ({err_msg}). Rotating key and retrying...")
                        self.rotate_key()
                        return self.detect_animal_gemini(image_path, retries - 1)
                    raise e

            text = response.text.strip()
            
            # Clean up potential markdown formatting
            if text.startswith("```json"):
                text = text[7:-3].strip()
            elif text.startswith("```"):
                text = text[3:-3].strip()
                
            data = json.loads(text)
            return {
                "animal": data.get("animal", "unknown"),
                "confidence": float(data.get("confidence", 0.0)),
                "reason": data.get("reason", ""),
                "method": "gemini"
            }
        except Exception as e:
            print(f"Gemini detection error: {e}")
            return {"animal": "unknown", "confidence": 0.0, "method": "gemini"}

    def detect_animal(self, image_path: str) -> dict:
        result = self.detect_animal_clip(image_path)
        
        if result["confidence"] >= 0.75:
            print(f"CLIP result accepted for {image_path} (Conf: {result['confidence']:.2f})")
            return result
        
        print(f"CLIP confidence low ({result['confidence']:.2f}). Falling back to Gemini...")
        fallback = self.detect_animal_gemini(image_path)
        return fallback

    def process_batch(self, image_paths: List[str], batch_size=32) -> List[np.ndarray]:
        embeddings = []
        for i in tqdm(range(0, len(image_paths), batch_size), desc="Batch Processing"):
            batch = image_paths[i:i+batch_size]
            for path in batch:
                embeddings.append(self.get_image_embedding(path))
        return embeddings

