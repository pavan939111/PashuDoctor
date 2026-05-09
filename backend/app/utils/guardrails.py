import os
import re
import json
import time
import hashlib
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import numpy as np

logger = logging.getLogger(__name__)

class InputSanitizer:
    PROMPT_INJECTION_PATTERNS = [
        "ignore previous instructions",
        "forget your instructions",
        "you are now",
        "act as",
        "pretend you are",
        "jailbreak",
        "dan mode",
        "ignore above",
        "system prompt",
        "override instructions",
        "new instructions",
        "disregard",
        "bypass",
        "you must now",
        "ignore all previous"
    ]

    HUMAN_MEDICAL_PATTERNS = [
        "my fever", "i have fever", "i have pain", "i am sick",
        "my child", "my husband", "my wife",
        "human", "person", "people", "man", "woman",
        "doctor for me", "medicine for me",
        "my symptoms", "i feel", "i am feeling"
    ]

    def sanitize_text(self, text: str) -> dict:
        original_length = len(text)
        # 1. Strip whitespace and replace multiple spaces
        text = " ".join(text.split())
        
        # 2. Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # 3. Truncate
        truncated = False
        if len(text) > 1000:
            text = text[:1000]
            truncated = True
            
        # 4. Detect injection
        injection_detected = False
        text_lower = text.lower()
        for pattern in self.PROMPT_INJECTION_PATTERNS:
            if pattern in text_lower:
                injection_detected = True
                break
                
        # 5. Detect human query
        human_query_detected = False
        for pattern in self.HUMAN_MEDICAL_PATTERNS:
            if pattern in text_lower:
                human_query_detected = True
                break
                
        return {
            "sanitized_text": text,
            "is_safe": not (injection_detected or human_query_detected),
            "injection_detected": injection_detected,
            "human_query_detected": human_query_detected,
            "original_length": original_length,
            "truncated": truncated
        }

    def validate_image_file(
        self,
        file_size_bytes: int,
        content_type: str,
        filename: str
    ) -> dict:
        ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp", "image/bmp"]
        MAX_SIZE_BYTES = 10 * 1024 * 1024  # 10MB
        MIN_SIZE_BYTES = 1024  # 1KB
        
        errors = []
        if content_type not in ALLOWED_TYPES:
            errors.append(f"Invalid file type: {content_type}. Allowed: {', '.join(ALLOWED_TYPES)}")
            
        if file_size_bytes > MAX_SIZE_BYTES:
            errors.append(f"File size too large: {file_size_bytes / (1024*1024):.2f}MB. Max: 10MB")
            
        if file_size_bytes < MIN_SIZE_BYTES:
            errors.append(f"File size too small: {file_size_bytes} bytes. Min: 1KB")
            
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "file_size_mb": round(file_size_bytes / (1024*1024), 2),
            "content_type": content_type
        }

    def check_animal_relevance(
        self,
        image_path: str,
        image_service
    ) -> dict:
        ANIMAL_PROMPTS = [
            "a photo of a farm animal",
            "a photo of livestock",
            "a photo of a cow buffalo goat or sheep",
            "a random object or landscape",
            "a photo of a person",
            "a blurry unclear image"
        ]
        
        # We assume image_service has a method to get similarity scores for custom prompts
        # For this implementation, we use the CLIP model in image_service
        try:
            import torch
            import clip
            from PIL import Image
            
            with Image.open(image_path) as img:
                image_input = image_service.preprocess(img.convert("RGB")).unsqueeze(0).to(image_service.device)
            text_tokens = clip.tokenize(ANIMAL_PROMPTS).to(image_service.device)
            
            with torch.no_grad():
                image_features = image_service.model.encode_image(image_input)
                text_features = image_service.model.encode_text(text_tokens)
                
                image_features /= image_features.norm(dim=-1, keepdim=True)
                text_features /= text_features.norm(dim=-1, keepdim=True)
                
                similarity = (100.0 * image_features @ text_features.T).softmax(dim=-1)
                values, indices = similarity[0].topk(len(ANIMAL_PROMPTS))
            
            probs = similarity[0].cpu().numpy()
            top_idx = int(indices[0])
            top_match = ANIMAL_PROMPTS[top_idx]
            confidence = float(values[0])
            
            # Non-animal indices are 3, 4, 5
            if top_idx >= 3:
                is_animal = False
                reason = f"Image does not appear to contain livestock (Matched: {top_match})"
            elif confidence < 0.20:
                is_animal = False
                reason = "Cannot identify livestock in image with sufficient confidence"
            else:
                is_animal = True
                reason = "OK"
                
            return {
                "is_animal": is_animal,
                "confidence": confidence,
                "reason": reason,
                "top_match": top_match
            }
        except Exception as e:
            logger.error(f"Animal relevance check failed: {e}")
            return {"is_animal": True, "confidence": 1.0, "reason": "Error running check, bypassing"}

class LLMOutputValidator:
    REQUIRED_DIAGNOSIS_FIELDS = [
        "primary_diagnosis", "alternative_diagnoses", "matching_symptoms",
        "immediate_precautions", "urgent_warning_signs", "herd_prevention",
        "farmer_advice", "vet_urgency", "severity"
    ]

    BANNED_DRUG_NAMES = [
        "oxytetracycline", "penicillin", "amoxicillin", "enrofloxacin",
        "gentamicin", "streptomycin", "dexamethasone", "prednisolone",
        "ivermectin", "albendazole", "fenbendazole", "levamisole",
        "oxytocin", "prostaglandin", "insulin", "mg/kg", "ml/kg",
        "dosage", "dose", "inject", "injection", "IV ", "IM ",
        "subcutaneous", "intramuscular", "intravenous"
    ]

    VALID_SEVERITIES = ["mild", "moderate", "severe", "emergency"]
    VALID_URGENCIES = ["immediate", "within_24h", "within_week", "monitor"]
    VALID_DISEASES = [
        "foot_and_mouth", "mastitis", "lumpy_skin_disease", 
        "blackquarter", "hemorrhagic_septicemia", "ppr", 
        "healthy", "unknown"
    ]

    def validate_diagnosis_response(self, response_text: str) -> dict:
        # 1. Parse JSON
        try:
            # Clean markdown if present
            text = response_text.strip()
            if text.startswith("```json"):
                text = text[7:-3].strip()
            elif text.startswith("```"):
                text = text[3:-3].strip()
            parsed = json.loads(text)
        except Exception:
            return {"valid": False, "error": "invalid_json", "raw": response_text}

        # 2. Check required fields
        missing = [f for f in self.REQUIRED_DIAGNOSIS_FIELDS if f not in parsed]
        if missing:
            return {"valid": False, "error": "missing_fields", "missing": missing}

        # 3. Validate values
        if parsed.get("severity") not in self.VALID_SEVERITIES:
            parsed["severity"] = "moderate"
        if parsed.get("vet_urgency") not in self.VALID_URGENCIES:
            parsed["vet_urgency"] = "within_24h"
            
        # 4. Drug name detection
        full_text = json.dumps(parsed).lower()
        found_drugs = [drug for drug in self.BANNED_DRUG_NAMES if drug.lower() in full_text]
        warnings = []
        if found_drugs:
            def sanitize_value(val):
                if isinstance(val, str):
                    for drug in found_drugs:
                        val = re.sub(re.escape(drug), "[REMOVED]", val, flags=re.IGNORECASE)
                    return val
                elif isinstance(val, list):
                    return [sanitize_value(v) for v in val]
                elif isinstance(val, dict):
                    return {k: sanitize_value(v) for k, v in val.items()}
                return val

            parsed = sanitize_value(parsed)
            warnings.append("Drug references removed by safety filter")
            logger.warning(f"Drug names detected and removed: {found_drugs}")

        return {
            "valid": True,
            "sanitized_response": parsed,
            "drug_names_removed": found_drugs,
            "fields_validated": True,
            "warnings": warnings
        }

    def validate_with_retry(self, prompt: str, gemini_service, system_prompt: str, image_paths: list = None, max_retries: int = 3) -> dict:
        current_prompt = prompt
        for attempt in range(max_retries):
            response = gemini_service.generate(current_prompt, system_prompt=system_prompt, image_paths=image_paths)
            if not response["success"]:
                continue
                
            validation = self.validate_diagnosis_response(response["text"])
            if validation["valid"]:
                return validation["sanitized_response"]
            else:
                logger.warning(f"Attempt {attempt+1} failed: {validation['error']}")
                if attempt < max_retries - 1:
                    current_prompt = prompt + f"\n\nIMPORTANT: Return ONLY valid JSON. No markdown, no explanation. Previous attempt failed because: {validation['error']}"

        return {
            "primary_diagnosis": "unknown",
            "alternative_diagnoses": [],
            "matching_symptoms": [],
            "immediate_precautions": [
                "Isolate the animal from the herd",
                "Ensure clean water and feed access",
                "Monitor for worsening symptoms"
            ],
            "urgent_warning_signs": [
                "If animal collapses: Call 1962 immediately",
                "If symptoms worsen: Contact veterinarian"
            ],
            "herd_prevention": ["Monitor all other animals for similar symptoms"],
            "farmer_advice": "Our AI could not make a confident diagnosis. Please contact a veterinarian. National Helpline: 1962 (Free, 24/7)",
            "vet_urgency": "within_24h",
            "severity": "moderate"
        }

class GuardrailAuditLogger:
    LOG_FILE = "data/logs/guardrail_audit.jsonl"

    def __init__(self):
        os.makedirs("data/logs", exist_ok=True)

    def log_event(self, event_type: str, case_id: str, details: dict, blocked: bool, ip: str = "unknown") -> None:
        ip_hash = hashlib.sha256(ip.encode()).hexdigest()[:12]
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "case_id": case_id,
            "blocked": blocked,
            "details": details,
            "ip_hash": ip_hash
        }
        with open(self.LOG_FILE, "a") as f:
            f.write(json.dumps(event) + "\n")

    def get_audit_summary(self) -> dict:
        if not os.path.exists(self.LOG_FILE):
            return {"total_events": 0, "by_type": {}, "blocked_requests": 0}
            
        counts = {}
        blocked = 0
        total = 0
        last_at = None
        
        with open(self.LOG_FILE, "r") as f:
            for line in f:
                try:
                    event = json.loads(line)
                    total += 1
                    e_type = event["event_type"]
                    counts[e_type] = counts.get(e_type, 0) + 1
                    if event["blocked"]:
                        blocked += 1
                    last_at = event["timestamp"]
                except:
                    continue
                    
        return {
            "total_events": total,
            "by_type": counts,
            "blocked_requests": blocked,
            "block_rate_percent": round((blocked / total * 100), 2) if total > 0 else 0,
            "last_event_at": last_at
        }
