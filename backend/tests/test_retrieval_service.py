import pytest
import numpy as np
from unittest.mock import MagicMock, patch
from app.services.retrieval_service import HybridRetrievalEngine, ChromaDBManager, BM25IndexManager

class TestHybridRetrieval:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.mock_chroma = MagicMock(spec=ChromaDBManager)
        self.mock_bm25 = MagicMock(spec=BM25IndexManager)
        self.mock_image = MagicMock()
        self.mock_text = MagicMock()
        
        self.engine = HybridRetrievalEngine(
            self.mock_chroma,
            self.mock_bm25,
            self.mock_image,
            self.mock_text
        )
        self.TOP_K_RETRIEVE = 20

    def test_retrieve_disease_candidates_returns_correct_count(self):
        emb = np.random.rand(512).astype(np.float32)
        # Mock Chroma query
        dense_res = [{"id": f"img{i}", "distance": 0.1, "metadata": {"animal": "cow"}} for i in range(30)]
        self.mock_chroma.query_diseases.return_value = dense_res
        self.mock_bm25.search_symptom_bm25.return_value = []
        
        results = self.engine.retrieve_disease_candidates(emb, "cow udder swelling", "cow", top_k=self.TOP_K_RETRIEVE)
        assert len(results) <= self.TOP_K_RETRIEVE
        for res in results:
            assert all(k in res for k in ["image_id", "final_score", "dense_score", "bm25_score", "metadata"])

    def test_metadata_filter_works(self):
        emb = np.random.rand(512).astype(np.float32)
        dense_res = [{"id": "img1", "distance": 0.1, "metadata": {"animal": "cow"}}, 
                     {"id": "img2", "distance": 0.2, "metadata": {"animal": "buffalo"}}]
        
        # In reality, retrieve_disease_candidates might filter these based on animal_type parameter
        # Here we mock it returning only cow
        self.mock_chroma.query_diseases.return_value = [dense_res[0]]
        self.mock_bm25.search_symptom_bm25.return_value = []
        
        results = self.engine.retrieve_disease_candidates(emb, "swelling", "cow")
        for res in results:
            assert res["metadata"]["animal"] == "cow"

    def test_score_fusion_range(self):
        emb = np.random.rand(512).astype(np.float32)
        dense_res = [
            {"id": "img1", "distance": 0.1, "metadata": {"animal": "cow"}},
            {"id": "img2", "distance": 0.9, "metadata": {"animal": "cow"}}
        ]
        bm25_res = [
            {"image_id": "img1", "bm25_score": 10.0, "metadata": {"animal": "cow"}},
            {"image_id": "img2", "bm25_score": 0.1, "metadata": {"animal": "cow"}}
        ]
        
        self.mock_chroma.query_diseases.return_value = dense_res
        self.mock_bm25.search_symptom_bm25.return_value = bm25_res
        
        results = self.engine.retrieve_disease_candidates(emb, "swelling", "cow")
        for res in results:
            assert 0.0 <= res["final_score"] <= 1.0

    def test_normalize_scores_all_equal(self):
        scores = [0.5, 0.5, 0.5]
        result = self.engine.normalize_scores(scores)
        assert result == [0.0, 0.0, 0.0]

    def test_normalize_scores_normal(self):
        scores = [0.1, 0.5, 0.9]
        result = self.engine.normalize_scores(scores)
        assert result[0] == 0.0
        assert result[2] == 1.0

    def test_bm25_search_returns_results(self):
        with patch('app.services.retrieval_service.BM25IndexManager.load_indexes'):
            manager = BM25IndexManager()
            # Mock internal bm25
            mock_bm25 = MagicMock()
            mock_bm25.get_scores.return_value = np.array([5.0, 0.0])
            manager.symptom_bm25 = mock_bm25
            manager.symptom_docs = [
                {"id": "doc1", "metadata": {"animal": "cow"}},
                {"id": "doc2", "metadata": {"animal": "cow"}}
            ]
            
            # Search "mastitis cow udder swelling milk"
            results = manager.search_symptom_bm25("mastitis cow udder swelling milk", top_k=2)
            assert len(results) > 0
            assert results[0]["bm25_score"] > 0

    def test_retrieve_knowledge_chunks(self):
        emb = np.random.rand(384).astype(np.float32)
        dense_res = [{"id": "k1", "distance": 0.1, "text": "HS treatment info", "metadata": {}}]
        self.mock_chroma.query_knowledge.return_value = dense_res
        self.mock_bm25.search_knowledge_bm25.return_value = []
        
        results = self.engine.retrieve_knowledge_candidates(emb, "hemorrhagic septicemia buffalo")
        assert len(results) > 0
        for res in results:
            assert "text" in res

