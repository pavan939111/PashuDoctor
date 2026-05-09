import os
import sys
import json
import pandas as pd
import numpy as np
import random

# Add backend to sys.path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.services.image_service import ImageService, TextEmbeddingService
from app.services.retrieval_service import ChromaDBManager

# Configuration
MANIFEST_PATH = os.path.join("data", "processed", "master_manifest.csv")

def main():
    print("Starting ChromaDB Verification...\n")
    
    image_service = ImageService()
    text_service = TextEmbeddingService()
    chroma = ChromaDBManager()
    
    results = {}

    # Test 1 — Collection health check
    print("Test 1: Collection Health Check")
    d_count = chroma.disease_collection.count()
    k_count = chroma.knowledge_collection.count()
    
    d_pass = d_count > 100
    k_pass = k_count > 20
    
    print(f" - Disease records: {d_count} ({'PASS' if d_pass else 'FAIL'})")
    print(f" - Knowledge records: {k_count} ({'PASS' if k_pass else 'FAIL'})")
    results["Test 1"] = d_pass and k_pass

    # Test 2 — Image query test
    print("\nTest 2: Image Query Test")
    if not os.path.exists(MANIFEST_PATH):
        print(" - FAIL: Manifest not found")
        results["Test 2"] = False
    else:
        df = pd.read_csv(MANIFEST_PATH)
        test_samples = []
        for animal in ["cow", "goat", "buffalo"]:
            sub = df[df["animal_type"] == animal]
            if not sub.empty:
                test_samples.append(sub.sample(1).iloc[0])
        
        t2_pass = True
        for sample in test_samples:
            img_path = sample["image_path"]
            animal = sample["animal_type"]
            
            emb = image_service.get_image_embedding(img_path)
            # Match the multimodal logic (pad text part)
            disease_text = text_service.get_disease_text(sample["disease_label"], animal)
            text_emb = text_service.get_text_embedding(disease_text)
            text_emb_512 = np.pad(text_emb, (0, 512 - 384), 'constant')
            combined = 0.6 * emb + 0.4 * text_emb_512
            combined = combined / np.linalg.norm(combined)
            
            top = chroma.query_diseases(combined, animal_type=animal, n_results=1)
            
            if top:
                top_res = top[0]
                match = top_res["metadata"]["animal"] == animal
                print(f" Query: {os.path.basename(img_path)} ({animal})")
                print(f" Top result: {top_res['metadata']['disease']} ({top_res['distance']:.3f})")
                print(f" Match: {'PASS' if match else 'FAIL'}")
                if not match: t2_pass = False
            else:
                print(f" Query: {os.path.basename(img_path)} -> No results")
                t2_pass = False
        results["Test 2"] = t2_pass

    # Test 3 — Text query test
    print("\nTest 3: Text Query Test")
    queries = [
        "cow with swollen udder and reduced milk",
        "buffalo with skin lumps and fever",
        "goat with oral sores and diarrhoea"
    ]
    t3_pass = True
    for q in queries:
        print(f" Query: '{q}'")
        emb = text_service.get_text_embedding(q)
        kb_res = chroma.query_knowledge(emb, n_results=3)
        if not kb_res:
            print("  - No results found")
            t3_pass = False
        for i, res in enumerate(kb_res):
            preview = res["text"][:50].replace("\n", " ") + "..."
            print(f"  [{i+1}] {res['metadata']['source']}: {preview} (Dist: {res['distance']:.3f})")
    results["Test 3"] = t3_pass

    # Test 4 — Metadata filter test
    print("\nTest 4: Metadata Filter Test")
    t4_pass = True
    for animal in ["cow", "goat"]:
        dummy_emb = np.random.rand(512).astype(np.float32)
        res = chroma.query_diseases(dummy_emb, animal_type=animal, n_results=5)
        for r in res:
            if r["metadata"]["animal"] != animal:
                t4_pass = False
                print(f" - FAIL: Found {r['metadata']['animal']} in {animal} query")
                break
        if t4_pass:
            print(f" - Filter '{animal}': PASS")
    results["Test 4"] = t4_pass

    # Test 5 — Embedding dimension check
    print("\nTest 5: Embedding Dimension Check")
    t5_pass = True
    # Check Disease
    d_data = chroma.disease_collection.get(limit=5, include=["embeddings"])
    if d_data["embeddings"] is not None and len(d_data["embeddings"]) > 0:
        for emb in d_data["embeddings"]:
            if len(emb) != 512:
                t5_pass = False
                print(f" - FAIL: Disease embedding dim is {len(emb)}")
    # Check Knowledge
    k_data = chroma.knowledge_collection.get(limit=5, include=["embeddings"])
    if k_data["embeddings"] is not None and len(k_data["embeddings"]) > 0:
        for emb in k_data["embeddings"]:
            if len(emb) != 384:
                t5_pass = False
                print(f" - FAIL: Knowledge embedding dim is {len(emb)}")
    
    if t5_pass:
        print(" - All dimensions consistent: PASS")
    results["Test 5"] = t5_pass

    # Final Report
    passed_count = sum(1 for v in results.values() if v)
    print("\n" + "="*45)
    print(f"Tests passed: {passed_count} / 5")
    ready = "YES" if passed_count == 5 else "NO"
    print(f"ChromaDB ready for retrieval: {ready}")
    print("="*45)

if __name__ == "__main__":
    main()
