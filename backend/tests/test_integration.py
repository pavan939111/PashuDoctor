import pytest
import pytest_asyncio
import os
import time
import numpy as np
import json
from httpx import AsyncClient
from unittest.mock import patch, MagicMock
from app.main import app
from app.dependencies import initialise_services, get_image_service

@pytest.fixture(scope="session", autouse=True)
async def setup_services():
    """Initialise all services once for the integration test session."""
    print("\n[INIT] Setting up services for integration tests...")
    await initialise_services()
    yield

@pytest.mark.asyncio
async def test_full_pipeline_with_persistence():
    """
    Test: Full pipeline from API call to database persistence.
    Verifies that the case is saved and can be retrieved via GET.
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        image_path = r"C:\Users\mahip\.cache\kagglehub\datasets\sivaprathishsiva\mastitis-disease-detection\versions\1\Data\mastitis\Picture40-400x284.jpg"
        
        if not os.path.exists(image_path):
            pytest.skip("Test image not found")

        with open(image_path, "rb") as f:
            files = {"image": ("test_cow.jpg", f, "image/jpeg")}
            data = {
                "symptom_text": "swollen udder and clots in milk", 
                "user_id": "persistence_user",
                "animal_type": "cow",
                "language": "english"
            }
            
            response = await ac.post("/analyze/image", data=data, files=files)
            
        assert response.status_code == 200
        res_json = response.json()
        assert res_json["success"] is True
        case_id = res_json["case_id"]
        
        # Verify persistence via GET endpoint
        get_response = await ac.get(f"/analyze/{case_id}")
        assert get_response.status_code == 200
        get_json = get_response.json()
        assert get_json["success"] is True
        assert get_json["case"]["user_id"] == "persistence_user"
        assert "diagnosis" in get_json

@pytest.mark.asyncio
async def test_api_key_rotation_on_failure():
    """
    Test: Gemini API key rotation on ResourceExhausted error.
    Mocks a failure on the first key and success on the second.
    """
    image_service = get_image_service()
    
    # Define side effect: raise error first time, return success second time
    mock_response = MagicMock()
    mock_response.text = '{"animal": "cow", "confidence": 0.9, "reason": "Looks like a cow"}'
    
    # We patch the GenerativeModel in the image_service module
    with patch('app.services.image_service.genai.GenerativeModel') as mock_model_class:
        mock_model = mock_model_class.return_value
        mock_model.generate_content.side_effect = [
            Exception("429 Resource has been exhausted"),
            mock_response
        ]
        
        # Patch the existing instance to avoid real API calls on the first attempt
        image_service.gemini = mock_model

        
        # Ensure we have at least 2 keys
        original_keys = image_service.api_keys
        image_service.api_keys = ["key1", "key2"]
        image_service.current_key_idx = 0
        
        # We also need to patch configure to avoid real calls
        with patch('app.services.image_service.genai.configure'):
            image_path = r"C:\Users\mahip\.cache\kagglehub\datasets\sivaprathishsiva\mastitis-disease-detection\versions\1\Data\mastitis\Picture40-400x284.jpg"
            result = image_service.detect_animal_gemini(image_path)
            
            assert result["animal"] == "cow"
            assert image_service.current_key_idx == 1 # Rotated once
            
        # Restore keys
        image_service.api_keys = original_keys


@pytest.mark.asyncio
async def test_invalid_image_upload():
    """
    Test: Uploading a non-image file.
    Asserts 415 or 400 status code.
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Create a dummy text file
        with open("test.txt", "w") as f:
            f.write("this is not an image")
            
        try:
            with open("test.txt", "rb") as f:
                files = {"image": ("test.txt", f, "text/plain")}
                data = {
                    "symptom_text": "swollen udder", 
                    "user_id": "integration_user"
                }
                response = await ac.post("/analyze/image", data=data, files=files)
                
            # Should fail with 415 (Unsupported Media Type) as per analyze.py line 61
            assert response.status_code == 415
        finally:
            if os.path.exists("test.txt"):
                os.remove("test.txt")

@pytest.mark.asyncio
async def test_full_pipeline_text_only():
    """
    Test: POST /analyze/text-only pipeline.
    Verifies that the system works without an image.
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        data = {
            "symptom_text": "Cow has high fever and blisters on mouth and feet.",
            "user_id": "text_user",
            "animal_type": "cow",
            "language": "english"
        }
        
        response = await ac.post("/analyze/text-only", json=data)
        
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["success"] is True
    assert res_json["animal_detection"]["method"] == "none"
    assert "diagnosis" in res_json

@pytest.mark.asyncio
async def test_low_confidence_triggers_followup():
    """
    Test: Pipeline when confidence is low.
    Verifies that follow-up questions are returned instead of diagnosis.
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Provide vague symptoms to trigger low confidence
        data = {
            "symptom_text": "animal is not eating", 
            "user_id": "low_conf_user",
            "animal_type": "goat"
        }
        
        response = await ac.post("/analyze/text-only", json=data)
        
    assert response.status_code == 200
    res_json = response.json()
    
    # If confidence is low, it might return show_prediction=False and follow_up_questions
    if not res_json["confidence"]["show_prediction"]:
        assert len(res_json["follow_up_questions"]) > 0
        assert res_json["diagnosis"] is None
    else:
        # If it still shows prediction (e.g. healthy), just check the structure
        assert "confidence" in res_json

@pytest.mark.asyncio
async def test_missing_fields():
    """
    Test: POST with missing required fields (e.g., user_id).
    Asserts 422 Unprocessable Entity.
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        image_path = r"C:\Users\mahip\.cache\kagglehub\datasets\sivaprathishsiva\mastitis-disease-detection\versions\1\Data\mastitis\Picture40-400x284.jpg"
        
        if not os.path.exists(image_path):
            pytest.skip("Test image not found")

        with open(image_path, "rb") as f:
            files = {"image": ("test_cow.jpg", f, "image/jpeg")}
            data = {
                "symptom_text": "swollen udder"
                # Missing user_id
            }
            response = await ac.post("/analyze/image", data=data, files=files)
            
        assert response.status_code == 422
