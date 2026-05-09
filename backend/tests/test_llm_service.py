import pytest
from unittest.mock import MagicMock
from app.services.llm_service import LLMRouter
from app.utils.prompts import build_diagnosis_prompt, format_response_for_farmer

class TestLLMService:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.router = LLMRouter()

    def test_llm_router_routes_to_gemini_low_confidence(self):
        routing_context = {"confidence_score": 0.35}
        assert self.router.route(routing_context) == "gemini"

    def test_llm_router_routes_to_gemini_high_confidence(self):
        # We use Gemini for all confidence levels now
        routing_context = {"confidence_score": 0.85}
        assert self.router.route(routing_context) == "gemini"

    def test_build_diagnosis_prompt_contains_required_fields(self):
        # mock data
        mock_candidates = [{"metadata": {"disease": "Mastitis", "animal": "cow"}, "final_score": 0.8}]
        mock_chunks = [{"text": "Sample knowledge"}]
        mock_conf = {"percentage": 82}
        
        prompt = build_diagnosis_prompt(
            animal_type="cow",
            symptom_text="swollen udder",
            top_candidates=mock_candidates,
            knowledge_chunks=mock_chunks,
            confidence=mock_conf
        )
        
        assert "ANIMAL:" in prompt
        assert "REPORTED SYMPTOMS:" in prompt
        assert "RETRIEVED SIMILAR CASES:" in prompt
        assert "YOUR TASKS:" in prompt

    def test_format_response_for_farmer_structure(self):
        mock_diagnosis = {
            "primary_diagnosis": "Mastitis",
            "confidence_percentage": 85,
            "matching_symptoms": ["swollen udder"],
            "immediate_precautions": ["Clean the udder"],
            "urgent_warning_signs": ["High fever"],
            "farmer_advice": "Consult a vet."
        }
        output = format_response_for_farmer(mock_diagnosis)
        
        assert "Diagnosis:" in output
        assert "Confidence:" in output
        assert "consult a" in output.lower()

