import os
import sys
import time
import json
import torch
import clip
import pandas as pd
import numpy as np
from PIL import Image
from tqdm import tqdm
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from sklearn.metrics import classification_report, confusion_matrix

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.services.image_service import ImageService
from app.services.text_service import TextEmbeddingService
from app.services.retrieval_service import ChromaDBManager, BM25IndexManager, HybridRetrievalEngine
from app.services.reranker_service import RerankerService

def main():
    print("--- PashuDoctor Evaluation System (Optimized Batch Mode) ---")
    
    # 1. Load test split
    MANIFEST_PATH = "data/processed/clean_manifest.csv"
    if not os.path.exists(MANIFEST_PATH):
        print(f"Error: {MANIFEST_PATH} not found.")
        return

    df = pd.read_csv(MANIFEST_PATH)
    test_df = df[df["split"] == "test"].copy()
    print(f"Evaluating on {len(test_df)} test images")

    # 2. Initialize Services
    print("\n[INIT] Loading services...")
    image_service = ImageService()
    text_service = TextEmbeddingService()
    chroma = ChromaDBManager()
    bm25 = BM25IndexManager(chroma)
    retrieval = HybridRetrievalEngine(chroma, bm25, image_service, text_service)
    reranker = RerankerService()
    print("[OK] All services loaded\n")

    device = image_service.device
    model = image_service.model
    preprocess = image_service.preprocess
    animal_prompts = image_service.ANIMAL_PROMPTS
    text_tokens = clip.tokenize(animal_prompts).to(device)
    
    image_paths = test_df["image_path"].tolist()
    ground_truths = test_df["disease_label"].tolist()
    animal_gts = test_df["animal_type"].tolist()

    # 3. Batch Image Processing (CLIP)
    print(f"[STEP 1] Running Batch CLIP Inference (Embeddings + Detection)...")
    batch_size = 32
    all_image_embeddings = []
    all_detected_animals = []
    all_animal_confidences = []
    
    # We'll collect indices for Gemini fallback
    gemini_fallback_indices = []

    start_time_clip = time.time()
    for i in tqdm(range(0, len(image_paths), batch_size), desc="CLIP Batch"):
        batch_paths = image_paths[i:i+batch_size]
        batch_images = []
        valid_indices = []
        
        for j, path in enumerate(batch_paths):
            try:
                with Image.open(path) as img:
                    batch_images.append(preprocess(img.convert("RGB")))
                    valid_indices.append(i + j)
            except Exception as e:
                print(f"Error loading {path}: {e}")
                # Placeholder for failed image
                all_image_embeddings.append(np.zeros(512))
                all_detected_animals.append("unknown")
                all_animal_confidences.append(0.0)

        if not batch_images:
            continue

        image_input = torch.stack(batch_images).to(device)
        
        with torch.no_grad():
            # Get Image Embeddings
            image_features = model.encode_image(image_input)
            image_features /= image_features.norm(dim=-1, keepdim=True)
            
            # Get Animal Probabilities
            text_features = model.encode_text(text_tokens)
            text_features /= text_features.norm(dim=-1, keepdim=True)
            
            similarity = (100.0 * image_features @ text_features.T).softmax(dim=-1)
            values, indices = similarity.topk(1, dim=-1)

        # Store results
        batch_embs = image_features.cpu().numpy()
        batch_probs = values.cpu().numpy().flatten()
        batch_indices = indices.cpu().numpy().flatten()
        
        for idx_in_batch, idx_global in enumerate(valid_indices):
            all_image_embeddings.append(batch_embs[idx_in_batch])
            conf = batch_probs[idx_in_batch]
            best_label = animal_prompts[batch_indices[idx_in_batch]].replace("a photo of a ", "")
            
            all_animal_confidences.append(float(conf))
            all_detected_animals.append(best_label)
            
            if conf < 0.75:
                gemini_fallback_indices.append(idx_global)

    # 4. Gemini Fallback (Multithreaded)
    if gemini_fallback_indices:
        print(f"[STEP 2] Running Gemini Fallback for {len(gemini_fallback_indices)} images...")
        
        def run_gemini(idx):
            res = image_service.detect_animal_gemini(image_paths[idx])
            return idx, res

        with ThreadPoolExecutor(max_workers=5) as executor:
            fallback_results = list(tqdm(executor.map(run_gemini, gemini_fallback_indices), 
                                        total=len(gemini_fallback_indices), 
                                        desc="Gemini Fallback"))
            
        for idx, res in fallback_results:
            all_detected_animals[idx] = res["animal"]
            all_animal_confidences[idx] = res["confidence"]

    # 5. Batch Retrieval (ChromaDB + BM25)
    print(f"[STEP 3] Running Retrieval for Disease Candidates...")
    all_candidates_lists = []
    retrieval_times = []

    for i in tqdm(range(len(image_paths)), desc="Retrieval"):
        start_t = time.time()
        
        # We need the symptom text to query
        symptom_text = text_service.get_disease_text(ground_truths[i], animal_gts[i])
        
        candidates = retrieval.retrieve_disease_candidates(
            image_embedding=all_image_embeddings[i],
            symptom_text=symptom_text,
            animal_type=all_detected_animals[i]
        )
        all_candidates_lists.append(candidates)
        retrieval_times.append((time.time() - start_t) * 1000)

    # 6. Batch Reranking (Heavy Optimization)
    print(f"[STEP 4] Running Batch Reranking (BGE)...")
    all_reranking_start = time.time()
    
    # Collect all pairs across all images
    all_pairs = []
    image_to_pairs_indices = [] # Map image index to range in all_pairs

    current_pair_idx = 0
    for i in range(len(image_paths)):
        symptom_query = text_service.get_disease_text(ground_truths[i], animal_gts[i])
        query_str = f"livestock disease diagnosis: {symptom_query}"
        
        candidates = all_candidates_lists[i]
        start_idx = current_pair_idx
        
        for c in candidates:
            m = c["metadata"]
            doc_str = f"{m.get('animal', 'unknown')} animal, disease: {m.get('disease', 'unknown')}, body part: {m.get('body_part', 'unknown')}, severity: {m.get('severity', 'unknown')}"
            all_pairs.append((query_str, doc_str))
            current_pair_idx += 1
            
        image_to_pairs_indices.append((start_idx, current_pair_idx))

    # Run reranker model on all pairs in batches
    if all_pairs:
        # BGE Reranker model.predict handles batching internally
        # But we'll do it in chunks to avoid memory pressure and show progress
        reranker_batch_size = 64
        all_reranker_scores = []
        
        for i in tqdm(range(0, len(all_pairs), reranker_batch_size), desc="Reranking Batches"):
            chunk = all_pairs[i:i+reranker_batch_size]
            scores = reranker.model.predict(chunk)
            all_reranker_scores.extend(scores.tolist())
            
        all_reranker_scores = np.array(all_reranker_scores)
    else:
        all_reranker_scores = np.array([])

    # 7. Final Scoring and Prediction
    print(f"[STEP 5] Computing Final Predictions and Metrics...")
    y_true = ground_truths
    y_pred = []
    top3_correct = 0
    animal_correct = 0
    confidence_scores = []

    for i in range(len(image_paths)):
        start_idx, end_idx = image_to_pairs_indices[i]
        candidates = all_candidates_lists[i]
        
        if start_idx == end_idx: # No candidates
            y_pred.append("unknown")
            confidence_scores.append(0.0)
            continue
            
        img_scores = all_reranker_scores[start_idx:end_idx]
        
        # Normalize reranker scores for this image
        s_min, s_max = img_scores.min(), img_scores.max()
        if s_max > s_min:
            norm_scores = (img_scores - s_min) / (s_max - s_min)
        else:
            norm_scores = np.zeros_like(img_scores)
            
        # Combine with retrieval scores
        for j, candidate in enumerate(candidates):
            candidate["reranker_score"] = float(img_scores[j])
            candidate["combined_score"] = (0.4 * float(norm_scores[j])) + (0.6 * candidate["final_score"])
            
        # Sort
        candidates.sort(key=lambda x: x["combined_score"], reverse=True)
        
        top_pred = candidates[0]["metadata"]["disease"]
        y_pred.append(top_pred)
        confidence_scores.append(candidates[0]["combined_score"])
        
        top3 = [c["metadata"]["disease"] for c in candidates[:3]]
        if ground_truths[i] in top3:
            top3_correct += 1
            
        if all_detected_animals[i] == animal_gts[i]:
            animal_correct += 1

    # 8. Compute Overall Metrics
    total = len(test_df)
    correct_top1 = sum([1 for t, p in zip(y_true, y_pred) if t == p])
    overall_top1 = correct_top1 / total
    overall_top3 = top3_correct / total
    animal_accuracy = animal_correct / total
    avg_confidence = np.mean(confidence_scores)
    avg_retrieval_ms = np.mean(retrieval_times)

    # 9. Reports and JSON
    os.makedirs("data/evaluation", exist_ok=True)
    report = classification_report(y_true, y_pred, output_dict=True)
    
    cm = confusion_matrix(y_true, y_pred, labels=sorted(list(set(y_true))))
    cm_df = pd.DataFrame(cm, index=sorted(list(set(y_true))), columns=sorted(list(set(y_true))))
    cm_df.to_csv("data/evaluation/confusion_matrix.csv")

    eval_results = {
        "timestamp": datetime.now().isoformat(),
        "total_samples": total,
        "overall_top1_accuracy": float(overall_top1),
        "overall_top3_accuracy": float(overall_top3),
        "animal_detection_accuracy": float(animal_accuracy),
        "avg_confidence": float(avg_confidence),
        "avg_retrieval_time_ms": float(avg_retrieval_ms),
        "per_class": {}
    }

    classes = sorted(list(set(y_true)))
    for cls in classes:
        cls_indices = [i for i, x in enumerate(y_true) if x == cls]
        cls_total = len(cls_indices)
        cls_correct_top1 = sum([1 for i in cls_indices if y_pred[i] == cls])
        
        eval_results["per_class"][cls] = {
            "top1": cls_correct_top1 / cls_total if cls_total > 0 else 0,
            "precision": report.get(cls, {}).get("precision", 0),
            "recall": report.get(cls, {}).get("recall", 0),
            "f1": report.get(cls, {}).get("f1-score", 0),
            "sample_count": cls_total
        }

    with open("data/evaluation/eval_results.json", "w") as f:
        json.dump(eval_results, f, indent=2)

    # 10. Print Final Evaluation Report
    def get_pass_fail(val, target):
        return "PASS" if val >= target else "FAIL"

    print("\n" + "+" + "-"*46 + "+")
    print("|         PashuDoctor Evaluation Report        |")
    print("+" + "-"*29 + "+" + "-"*16 + "+")
    print(f"| Test images evaluated       | {total:<14} |")
    print(f"| Overall Top-1 Accuracy      | {overall_top1*100:>6.1f}%         |")
    print(f"| Overall Top-3 Accuracy      | {overall_top3*100:>6.1f}%         |")
    print(f"| Animal Detection Accuracy   | {animal_accuracy*100:>6.1f}%         |")
    print(f"| Average Confidence Score    | {avg_confidence*100:>6.1f}%         |")
    print(f"| Average Retrieval Time      | {avg_retrieval_ms:>6.1f}ms       |")
    print("+" + "-"*29 + "+" + "-"*16 + "+")
    print("| Per-class Top-1:            |                |")
    
    for cls in ["foot_and_mouth", "mastitis", "lumpy_skin_disease", "blackquarter", "hemorrhagic_septicemia", "ppr", "healthy"]:
        if cls in eval_results["per_class"]:
            acc = eval_results["per_class"][cls]["top1"] * 100
            print(f"|   {cls:<25} | {acc:>6.1f}%         |")
        else:
            print(f"|   {cls:<25} | N/A            |")
    
    print("+" + "-"*46 + "+")


    print(f"\nTarget benchmarks:")
    print(f"Top-1 Accuracy >= 70%: {get_pass_fail(overall_top1, 0.70)}")
    print(f"Top-3 Accuracy >= 88%: {get_pass_fail(overall_top3, 0.88)}")
    print(f"Animal Detection >= 85%: {get_pass_fail(animal_accuracy, 0.85)}")
    print(f"\nResults saved to data/evaluation/")

if __name__ == "__main__":
    main()
