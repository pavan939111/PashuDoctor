import math
from typing import List, Dict, Any, Optional
from app.config import get_settings

settings = get_settings()

def compute_confidence(
    image_similarity: float,
    text_similarity: float,
    symptom_match: float,
    reranker_score: float = 0.0
) -> Dict[str, Any]:
    """
    Inputs must be in 0.0 - 1.0 range.
    """
    # 0.5 visual + 0.3 text + 0.2 symptoms
    base_score = (0.5 * image_similarity + 
                  0.3 * text_similarity + 
                  0.2 * symptom_match)
    
    if reranker_score > 0:
        # CrossEncoder reranker gives a significant boost/penalty
        # Normalize reranker_score if needed, here we assume it's already a probability or normalized
        final_score = 0.7 * base_score + 0.3 * reranker_score
    else:
        final_score = base_score
        
    # Clamp
    final_score = max(0.0, min(1.0, final_score))
    
    return {
        "score": float(final_score),
        "percentage": int(round(final_score * 100)),
        "image_sim": float(image_similarity),
        "text_sim": float(text_similarity),
        "symptom_match": float(symptom_match),
        "reranker_score": float(reranker_score)
    }

def route_by_confidence(confidence_dict: Dict[str, Any]) -> Dict[str, Any]:
    score = confidence_dict["score"]
    
    # Thresholds: 0.35, 0.60, 0.85
    if score < 0.35:
        action = "ask_more"
        message = "Not enough information. Please answer a few questions."
        show_prediction = False
    elif 0.35 <= score < 0.60:
        action = "show_options"
        message = "Possible conditions identified. Please review."
        show_prediction = True
    elif 0.60 <= score < 0.85:
        action = "suggest"
        message = "Likely condition identified. Vet visit recommended."
        show_prediction = True
    else: # score >= 0.85
        action = "strong_suggest"
        message = "High confidence diagnosis. Consult vet immediately."
        show_prediction = True
        
    return {
        "action": action,
        "message": message,
        "show_prediction": show_prediction,
        "confidence": confidence_dict,
        "use_gemini_fallback": score < 0.40
    }

def compute_symptom_match(
    provided_symptoms: List[str],
    disease_symptoms: List[str]
) -> float:
    if not provided_symptoms or not disease_symptoms:
        return 0.0
        
    set_provided = set(s.lower().strip() for s in provided_symptoms)
    set_disease = set(s.lower().strip() for s in disease_symptoms)
    
    intersection = set_provided.intersection(set_disease)
    
    if not set_disease:
        return 0.0
        
    # Recall-based scoring: How many of the required symptoms were mentioned?
    # This is better for long user sentences.
    return float(len(intersection) / len(set_disease))

def extract_scores_from_retrieval(
    top_candidate: Dict[str, Any],
    retrieval_results: Dict[str, Any],
    provided_symptoms: List[str] = []
) -> Dict[str, Any]:
    # Extract values
    image_sim = top_candidate.get("dense_score", 0.0)
    # combined_score from reranker includes retrieval + rerank boost
    text_sim = top_candidate.get("combined_score", top_candidate.get("final_score", 0.0))
    reranker_score = top_candidate.get("reranker_score", 0.0)
    
    # Symptoms from metadata (comma separated string usually)
    meta = top_candidate.get("metadata", {})
    # In our manifest, disease_label is used. 
    # For actual symptoms, we'd ideally have them in metadata.
    # For now, let's assume we map disease_label to symptoms if not present
    # Normalise disease name
    disease = meta.get("disease", "unknown").lower().replace("-", "_")
    
    # Robust mapping for this utility
    DISEASE_SYMPTOM_MAP = {
        "foot_and_mouth": ["blisters", "sores", "fever", "drooling", "lameness", "limping", "mouth", "tongue", "hoof", "vesicles", "saliva"],
        "mastitis": ["swelling", "swollen", "hot", "painful", "clots", "blood", "udder", "milk", "pus", "redness", "hardness"],
        "lumpy_skin_disease": ["nodules", "lumps", "fever", "weight loss", "skin", "bumps"],
        "blackquarter": ["swelling", "swollen", "muscle", "crackling", "sudden death", "leg", "thigh"],
        "hemorrhagic_septicemia": ["fever", "swelling", "swollen", "throat", "breathing", "neck", "tongue"],
        "ppr": ["lesions", "diarrhoea", "pneumonia", "fever", "mouth", "nasal", "discharge"]
    }
    
    disease_symptoms = DISEASE_SYMPTOM_MAP.get(disease, [])
    symptom_match = compute_symptom_match(provided_symptoms, disease_symptoms)
    
    return {
        "image_similarity": image_sim,
        "text_similarity": text_sim,
        "symptom_match": symptom_match,
        "reranker_score": reranker_score
    }

class FollowUpQuestionGenerator:
    QUESTION_BANK = {
        "general": [
            "How long has the animal been showing symptoms?",
            "Is the animal eating and drinking normally?",
            "What is the animal's age and breed?",
            "Are other animals in the herd showing similar symptoms?",
            "Has the animal been vaccinated recently?"
        ],
        "foot_and_mouth": [
            "Are there blisters or sores visible on the mouth or hooves?",
            "Is the animal drooling excessively?",
            "Is the animal limping or reluctant to walk?"
        ],
        "mastitis": [
            "Is the udder swollen, hot, or painful to touch?",
            "Has milk production dropped suddenly?",
            "Is there any blood, clots, or unusual colour in the milk?"
        ],
        "lumpy_skin_disease": [
            "Are there raised skin nodules or lumps on the body?",
            "Are the lymph nodes visibly swollen?",
            "Has the animal lost significant weight recently?"
        ],
        "blackquarter": [
            "Is there swelling in the leg or shoulder muscles?",
            "Does the swollen area make a crackling sound when pressed?",
            "Did the animal appear healthy yesterday?"
        ],
        "hemorrhagic_septicemia": [
            "Is there swelling around the throat or neck?",
            "Is the animal having difficulty breathing?",
            "Did this start during or after the monsoon season?"
        ],
        "ppr": [
            "Are there sores or ulcers visible inside the mouth?",
            "Is the animal having diarrhoea?",
            "Is this a goat or sheep?"
        ]
    }

    def get_questions(
        self,
        action: str,
        disease_hint: str = None,
        answered: List[str] = []
    ) -> List[str]:
        questions = []
        
        # 1. Disease specific
        if disease_hint and disease_hint in self.QUESTION_BANK:
            specific = [q for q in self.QUESTION_BANK[disease_hint] if q not in answered]
            questions.extend(specific[:2])
            
        # 2. Fill with general
        remaining = 3 - len(questions)
        if remaining > 0:
            general = [q for q in self.QUESTION_BANK["general"] if q not in answered]
            questions.extend(general[:remaining])
            
        return questions[:3]
