import pytest
from app.utils.confidence import (
    compute_confidence, route_by_confidence, 
    compute_symptom_match, FollowUpQuestionGenerator
)

class TestConfidence:
    def test_compute_confidence_formula(self):
        # Expected: 0.5*0.8 + 0.3*0.6 + 0.2*0.7 = 0.4 + 0.18 + 0.14 = 0.72
        result = compute_confidence(
            image_similarity=0.8,
            text_similarity=0.6,
            symptom_match=0.7
        )
        assert abs(result["score"] - 0.72) < 0.001

    def test_confidence_clamped_to_one(self):
        result = compute_confidence(1.0, 1.0, 1.0)
        assert result["score"] <= 1.0

    def test_route_ask_more(self):
        # confidence score = 0.35
        conf = {"score": 0.35, "percentage": 35}
        routing = route_by_confidence(conf)
        assert routing["action"] == "ask_more"
        assert routing["show_prediction"] == False

    def test_route_show_options(self):
        conf = {"score": 0.62, "percentage": 62}
        routing = route_by_confidence(conf)
        assert routing["action"] == "show_options"

    def test_route_suggest(self):
        conf = {"score": 0.82, "percentage": 82}
        routing = route_by_confidence(conf)
        assert routing["action"] == "suggest"

    def test_route_strong_suggest(self):
        conf = {"score": 0.93, "percentage": 93}
        routing = route_by_confidence(conf)
        assert routing["action"] == "strong_suggest"

    def test_gemini_fallback_triggered(self):
        conf = {"score": 0.38, "percentage": 38}
        routing = route_by_confidence(conf)
        assert routing["use_gemini_fallback"] == True

    def test_symptom_match_jaccard(self):
        provided = ["fever", "swelling", "milk"]
        disease = ["fever", "swelling", "udder", "milk", "clots"]
        # Jaccard = Intersection / Union = 3 / 5 = 0.60
        result = compute_symptom_match(provided, disease)
        assert abs(result - 0.60) < 0.001

    def test_follow_up_generator_no_repeats(self):
        gen = FollowUpQuestionGenerator()
        q1 = gen.get_questions("ask_more", "mastitis", answered=[])
        q2 = gen.get_questions("ask_more", "mastitis", answered=q1)
        q3 = gen.get_questions("ask_more", "mastitis", answered=q1 + q2)
        
        all_questions = q1 + q2 + q3
        assert len(all_questions) == len(set(all_questions))

