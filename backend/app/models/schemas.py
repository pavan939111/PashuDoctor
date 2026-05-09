from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
from datetime import datetime

# 1. Request Models

class AnalyzeRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=100)
    symptom_text: str = Field(..., min_length=3, max_length=1000)
    animal_type: str | None = None
    case_id: str | None = None
    language: str = "english"

    @field_validator("animal_type")
    @classmethod
    def validate_animal(cls, v: str | None) -> str | None:
        if v is not None:
            v_lower = v.lower()
            if v_lower not in ["cow", "buffalo", "goat", "sheep", "unknown"]:
                raise ValueError("animal_type must be one of cow/buffalo/goat/sheep/unknown")
            return v_lower
        return v

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        v_lower = v.lower()
        if v_lower not in ["english", "hindi", "tamil"]:
            raise ValueError("language must be one of english/hindi/tamil")
        return v_lower

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "farmer_12345",
                "symptom_text": "My cow has a swollen udder and milk production has decreased with some clots.",
                "animal_type": "cow",
                "language": "english"
            }
        }
    )

class ChatRequest(BaseModel):
    case_id: str
    user_id: str = Field(..., min_length=1, max_length=100)
    message: str = Field(..., min_length=1, max_length=1000)
    answered_questions: list[dict] = []
    model_config = ConfigDict()

class FeedbackRequest(BaseModel):
    case_id: str
    feedback_correct: bool
    farmer_note: str = ""
    model_config = ConfigDict()

class FollowUpRequest(BaseModel):
    case_id: str
    user_id: str = Field(..., min_length=1, max_length=100)
    question_answers: list[dict]
    symptom_text: str = Field(..., min_length=3, max_length=1000)
    model_config = ConfigDict()

# 2. Response Models

class AnimalDetectionResult(BaseModel):
    animal: str = "unknown"
    confidence: float = 0.0
    method: str = "unknown"
    model_config = ConfigDict()

class DiseaseCandidate(BaseModel):
    disease: str
    animal: str
    body_part: str
    severity: str
    final_score: float
    reranker_score: float
    model_config = ConfigDict()

class ConfidenceResult(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0)
    percentage: int
    action: str
    message: str
    show_prediction: bool
    model_config = ConfigDict()

class DiagnosisResult(BaseModel):
    primary_diagnosis: str
    alternative_diagnoses: list[str]
    matching_symptoms: list[str]
    immediate_precautions: list[str]
    urgent_warning_signs: list[str]
    herd_prevention: list[str]
    farmer_advice: str
    vet_urgency: str
    severity: str
    formatted_response: str
    model_config = ConfigDict()

class AnalyzeResponse(BaseModel):
    case_id: str
    animal_detection: AnimalDetectionResult
    confidence: ConfidenceResult
    diagnosis: DiagnosisResult | None = None
    follow_up_questions: list[str]
    top_candidates: list[DiseaseCandidate]
    retrieval_time_ms: float
    llm_time_ms: float
    model_used: str
    success: bool
    error: str | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "case_id": "550e8400-e29b-41d4-a716-446655440000",
                "animal_detection": {
                    "animal": "cow",
                    "confidence": 0.97,
                    "method": "clip"
                },
                "confidence": {
                    "score": 0.82,
                    "percentage": 82,
                    "action": "suggest",
                    "message": "Likely condition identified. Vet visit recommended.",
                    "show_prediction": True
                },
                "diagnosis": {
                    "primary_diagnosis": "Bovine Mastitis",
                    "alternative_diagnoses": ["Udder Edema", "Traumatic Injury"],
                    "matching_symptoms": ["swollen udder", "clots in milk", "reduced yield"],
                    "immediate_precautions": ["Isolate the animal", "Clean the udder with warm water", "Do not feed milk to calves"],
                    "urgent_warning_signs": ["Blood in milk", "High fever", "Animal unable to stand"],
                    "herd_prevention": ["Maintain dry bedding", "Proper milking hygiene", "Post-milking teat dipping"],
                    "farmer_advice": "Keep the cow in a clean, dry area and ensure complete milking.",
                    "vet_urgency": "High",
                    "severity": "Moderate",
                    "formatted_response": "Your cow shows signs of Mastitis. Please isolate her and maintain strict hygiene..."
                },
                "follow_up_questions": [],
                "top_candidates": [
                    {
                        "disease": "Mastitis",
                        "animal": "cow",
                        "body_part": "udder",
                        "severity": "moderate",
                        "final_score": 0.82,
                        "reranker_score": 0.88
                    }
                ],
                "retrieval_time_ms": 145.2,
                "llm_time_ms": 1200.0,
                "model_used": "gemini-1.5-flash",
                "success": True,
                "error": None
            }
        }
    )

class ChatResponse(BaseModel):
    case_id: str
    response: str
    updated_confidence: ConfidenceResult | None = None
    follow_up_questions: list[str]
    diagnosis_updated: bool
    success: bool
    model_config = ConfigDict()

class CaseHistoryItem(BaseModel):
    case_id: str
    animal_type: str
    primary_diagnosis: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    severity: str
    vet_urgency: str
    created_at: str
    model_config = ConfigDict()

class HistoryResponse(BaseModel):
    user_id: str
    cases: list[CaseHistoryItem]
    total: int
    model_config = ConfigDict()
