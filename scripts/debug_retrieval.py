import os
import sys
import numpy as np
import asyncio
import torch
import clip

# Add backend to sys.path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.dependencies import initialise_services, get_image_service, get_text_service, get_retrieval, get_reranker

async def debug_retrieval():
    await initialise_services()
    retrieval = get_retrieval()
    image_service = get_image_service()
    reranker = get_reranker()
    
    print("\n--- Retrieval & Rerank Debugger ---")
    
    symptom_text = "My cow has developed small, hard lumps and nodules all over its neck and back. It has a slight fever and is eating less than usual."
    animal_type = "cow"
    
    with torch.no_grad():
        tokens = clip.tokenize(["a photo of a cow with lumps"]).to(image_service.device)
        image_emb = image_service.model.encode_text(tokens).cpu().numpy().flatten()
        image_emb = image_emb / np.linalg.norm(image_emb)
        
    print(f"Query: {symptom_text}")
    
    # 1. Retrieval
    results_raw = retrieval.retrieve_all(["fake_path"], symptom_text, animal_type)
    # Mocking retrieval.retrieve_all because it needs real images normally, 
    # but we just want to see the candidates.
    
    candidates = retrieval.retrieve_disease_candidates(image_emb, symptom_text, animal_type)
    
    # 2. Reranking
    reranked = reranker.rerank_all(symptom_text, {"disease_candidates": candidates})
    
    print(f"\nFound {len(candidates)} candidates.")
    for i, res in enumerate(reranked["disease_candidates"][:3]):
        print(f"\nCandidate {i+1}: {res['metadata'].get('disease')}")
        print(f"  Final Score: {res['final_score']:.4f}")
        print(f"  Reranker Score: {res.get('reranker_score', 0.0):.4f}")
        print(f"  Dense Score: {res.get('dense_score', 0.0):.4f}")

if __name__ == "__main__":
    asyncio.run(debug_retrieval())
