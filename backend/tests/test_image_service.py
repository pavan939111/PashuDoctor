import pytest
import os
import numpy as np
from PIL import Image
from unittest.mock import patch, MagicMock
from app.services.image_service import ImageService

class TestImageService:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.image_service = ImageService()
        # Use a real test image path from the test split
        self.test_img_path = r"C:\Users\mahip\.cache\kagglehub\datasets\devang03mgr\cattle-diseases-datasets\versions\1\Cows datasets\healthy\BrownSwisscattle25.jpg"
        self.cow_img_path = r"C:\Users\mahip\.cache\kagglehub\datasets\devang03mgr\cattle-diseases-datasets\versions\1\Cows datasets\lumpy\img1886_jpg.rf.2078cf3e852f6386e3d924db37a84bcd.jpg"

    def test_get_image_embedding_returns_correct_shape(self):
        if not os.path.exists(self.test_img_path):
            pytest.skip(f"Test image not found: {self.test_img_path}")
        
        embedding = self.image_service.get_image_embedding(self.test_img_path)
        assert embedding.shape == (512,)
        assert embedding.dtype == np.float32
        # Assert np.linalg.norm(embedding) ≈ 1.0 (normalized)
        assert np.linalg.norm(embedding) == pytest.approx(1.0, abs=1e-3)

    def test_get_image_embedding_corrupt_file(self):
        corrupt_path = "corrupt_test.txt"
        with open(corrupt_path, "w") as f:
            f.write("not an image")
        
        try:
            # Should return zeros instead of crashing
            embedding = self.image_service.get_image_embedding(corrupt_path)
            assert np.array_equal(embedding, np.zeros(512))
        finally:
            if os.path.exists(corrupt_path):
                os.remove(corrupt_path)

    def test_detect_animal_clip_cow(self):
        if not os.path.exists(self.cow_img_path):
            pytest.skip(f"Cow image not found: {self.cow_img_path}")
        
        result = self.image_service.detect_animal_clip(self.cow_img_path)
        assert result["animal"] == "cow"
        assert result["confidence"] > 0.60

    def test_detect_animal_fallback_to_gemini(self):
        low_conf_result = {"animal": "cow", "confidence": 0.30, "method": "clip"}
        gemini_result = {"animal": "cow", "confidence": 0.90, "method": "gemini"}
        
        with patch.object(ImageService, 'detect_animal_clip', return_value=low_conf_result):
            with patch.object(ImageService, 'detect_animal_gemini', return_value=gemini_result) as mock_gemini:
                result = self.image_service.detect_animal(self.test_img_path)
                assert result["method"] == "gemini"
                assert mock_gemini.called

    def test_check_image_quality_valid(self):
        if not os.path.exists(self.test_img_path):
            pytest.skip("Test image not found")
            
        result = self.image_service.check_image_quality(self.test_img_path)
        assert result["valid"] == True

    def test_check_image_quality_too_small(self):
        small_path = "small_test.jpg"
        img = Image.new('RGB', (32, 32), color='black')
        img.save(small_path)
        
        try:
            result = self.image_service.check_image_quality(small_path)
            assert result["valid"] == False
            assert "size" in result["reason"].lower()
        finally:
            if os.path.exists(small_path):
                os.remove(small_path)

    def test_process_batch(self):
        if not os.path.exists(self.test_img_path):
            pytest.skip("Test image not found")
            
        image_paths = [self.test_img_path] * 5
        result = self.image_service.process_batch(image_paths)
        assert len(result) == 5
        for emb in result:
            assert emb.shape == (512,)

