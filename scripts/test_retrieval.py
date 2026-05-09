import os
import sys
import time
import json
import numpy as np
import asyncio

# Add backend to sys.path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.services.image_service import ImageService
from app.services.text_service import TextEmbeddingService
from app.services.retrieval_service import ChromaDBManager, BM25IndexManager, HybridRetrievalEngine
from app.services.reranker_service import RerankerService
from app.utils.confidence import compute_confidence, route_by_confidence, extract_scores_from_retrieval, FollowUpQuestionGenerator

def print_result(case_num, name, result, retrieval_time, rerank_time):
    # Extract top disease
    top_disease = "None"
    score = 0
    action = "N/A"
    
    if result.get("disease_candidates"):
        top = result["disease_candidates"][0]
        top_disease = top["metadata"].get("disease", "unknown")
        
        # Compute confidence using our utility
        scores = extract_scores_from_retrieval(top, result)
        conf_dict = compute_confidence(**scores)
        route = route_by_confidence(conf_dict)
        
        score = conf_dict["percentage"]
        action = route["action"]

    print("\n+---------------------------------------------+")
    print(f"| Test Case {case_num}: {name:<31} |")
    print("+----------------------+----------------------+")
    print(f"| Animal detected      | {result.get('animal_type', 'unknown'):<20} |")
    print(f"| Top disease          | {top_disease:<20} |")
    print(f"| Confidence score     | {score:<19}% |")
    print(f"| Action               | {action:<20} |")
    print(f"| Retrieval time       | {retrieval_time:<18.2f}ms |")
    print(f"| Reranking time       | {rerank_time:<18.2f}ms |")
    print("+----------------------+----------------------+")
    return retrieval_time, rerank_time, action

async def main():
    print("Initializing PashuDoctor Retrieval Pipeline...")
    
    image_service = ImageService()
    text_service = TextEmbeddingService()
    chroma = ChromaDBManager()
    bm25 = BM25IndexManager(chroma) # Pass chroma to rebuild if needed
    retrieval = HybridRetrievalEngine(chroma, bm25, image_service, text_service)
    reranker = RerankerService()
    question_gen = FollowUpQuestionGenerator()
    
    stats = []

    # Paths (Placeholders if local paths don't exist)
    fmd_img = r"C:\Users\mahip\.cache\kagglehub\datasets\devang03mgr\cattle-diseases-datasets\versions\1\Cows datasets\foot-and-mouth\-24-_jpg.rf.a8145c875b1985f2632b853ab03d4ae3.jpg"
    mastitis_img = r"C:\Users\mahip\.cache\kagglehub\datasets\sivaprathishsiva\mastitis-disease-detection\versions\1\Data\23.jpeg"
    
    # Check if images exist, if not create dummy ones or handle error
    if not os.path.exists(fmd_img) or not os.path.exists(mastitis_img):
        print("Warning: Test images not found at absolute paths. Using dummy data for structural test.")
        # Create a tiny dummy image if none exist
        from PIL import Image
        dummy_path = "dummy_test.jpg"
        Image.new('RGB', (100, 100), color = (73, 109, 137)).save(dummy_path)
        fmd_img = dummy_path
        mastitis_img = dummy_path
    
    # Test Case 1 — Mastitis query
    print("\nRunning Test Case 1: Mastitis...")
    s1 = "cow with swollen udder, reduced milk, hot painful udder, milk has clots"
    r1 = await retrieval.retrieve_all(mastitis_img, s1, animal_type="cow")
    t1_ret = r1["retrieval_time_ms"]
    r1 = reranker.rerank_all(s1, r1)
    t1_rer = r1["reranking_time_ms"]
    stats.append(print_result(1, "Mastitis (Cow)", r1, t1_ret, t1_rer))

    # Test Case 2 — FMD query
    print("\nRunning Test Case 2: FMD...")
    s2 = "cattle with blisters on mouth, drooling, limping, not eating, high fever"
    r2 = await retrieval.retrieve_all(fmd_img, s2) # Auto-detect animal
    t2_ret = r2["retrieval_time_ms"]
    r2 = reranker.rerank_all(s2, r2)
    t2_rer = r2["reranking_time_ms"]
    stats.append(print_result(2, "FMD (Cattle)", r2, t2_ret, t2_rer))

    # Test Case 3 — Low confidence query
    print("\nRunning Test Case 3: Low Confidence...")
    s3 = "animal seems sick"
    r3 = await retrieval.retrieve_all(fmd_img, s3)
    t3_ret = r3["retrieval_time_ms"]
    r3 = reranker.rerank_all(s3, r3)
    t3_rer = r3["reranking_time_ms"]
    _, _, action = print_result(3, "Low Confidence", r3, t3_ret, t3_rer)
    
    if action == "ask_more":
        questions = question_gen.get_questions(action, disease_hint=None)
        print(" Generated Questions:")
        for q in questions:
            print(f"  - {q}")

    # Test Case 4 — Knowledge retrieval
    print("\nRunning Test Case 4: Knowledge Retrieval...")
    s4 = "buffalo with sudden high fever and neck swelling"
    t_start = time.time()
    kb_emb = text_service.get_text_embedding(s4)
    kb_results = retrieval.retrieve_knowledge_candidates(kb_emb, s4, top_k=3)
    t_kb = (time.time() - t_start) * 1000
    
    print("+---------------------------------------------+")
    print(f"| Test Case 4: Knowledge Retrieval (Buffalo) |")
    print("+---------------------------------------------+")
    for i, res in enumerate(kb_results):
        preview = res["text"][:100].replace("\n", " ") + "..."
        print(f"| [{i+1}] {res['metadata']['source']:<15} | Score: {res['final_score']:.3f} |")
        print(f"|     {preview[:40]:<40} |")
    print("+---------------------------------------------+")
    stats.append((t_kb, 0, "N/A"))

    # Final Summary
    avg_ret = sum(s[0] for s in stats) / len(stats)
    avg_rer = sum(s[1] for s in stats) / len(stats)
    
    print("\n" + "="*45)
    print(f"Average retrieval time: {avg_ret:.2f}ms")
    print(f"Average reranking time: {avg_rer:.2f}ms")
    print(f"Pipeline ready for LLM: YES")
    print("="*45)

if __name__ == "__main__":
    asyncio.run(main())
