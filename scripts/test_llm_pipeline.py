import os
import sys
import asyncio
import time
import json
import numpy as np

# Add backend to sys.path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.services.llm_service import LLMRouter
from app.services.memory_service import MemoryService
from app.services.retrieval_service import ChromaDBManager, BM25IndexManager, HybridRetrievalEngine
from app.services.image_service import ImageService, TextEmbeddingService
from app.services.reranker_service import RerankerService
from app.utils.prompts import build_diagnosis_prompt, format_response_for_farmer, SYSTEM_PROMPT
from app.utils.confidence import compute_confidence, route_by_confidence, extract_scores_from_retrieval, FollowUpQuestionGenerator
from app.database import engine, Base, async_session

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables initialized.")

async def main():
    print("Initializing LLM Pipeline Test...")
    await init_db()
    
    # 1. Init Services
    image_service = ImageService()
    text_service = TextEmbeddingService()
    chroma = ChromaDBManager()
    bm25 = BM25IndexManager(chroma)
    retrieval = HybridRetrievalEngine(chroma, bm25, image_service, text_service)
    reranker = RerankerService()
    llm_router = LLMRouter()
    memory = MemoryService(async_session, chroma)
    question_gen = FollowUpQuestionGenerator()
    
    test_results = {}
    total_time = 0
    
    # --- Test Case 1: High Confidence Diagnosis ---
    print("\n[Test 1] High Confidence Diagnosis (Mastitis)...")
    mastitis_img = r"C:\Users\mahip\.cache\kagglehub\datasets\sivaprathishsiva\mastitis-disease-detection\versions\1\Data\23.jpeg"
    s1 = "cow with swollen udder, reduced milk, hot painful udder, milk has clots"
    
    r1 = retrieval.retrieve_all(mastitis_img, s1, animal_type="cow")
    r1 = reranker.rerank_all(s1, r1)
    
    top = r1["disease_candidates"][0]
    provided_symptoms = [s.strip() for s in s1.replace(",", " ").split()]
    scores = extract_scores_from_retrieval(top, r1, provided_symptoms=provided_symptoms)
    conf = compute_confidence(**scores)
    
    prompt = build_diagnosis_prompt("cow", s1, r1["disease_candidates"][:3], r1["knowledge_chunks"][:3], conf)
    
    start = time.time()
    response = llm_router.generate(prompt, system_prompt=SYSTEM_PROMPT)
    duration = (time.time() - start) * 1000
    total_time += duration
    
    print(f" Raw LLM Response: {response['text'][:100]}...")
    
    try:
        text = response["text"].strip()
        if text.startswith("```json"): text = text[7:-3].strip()
        elif text.startswith("```"): text = text[3:-3].strip()
        
        # Sometimes there's text before or after JSON
        start_idx = text.find("{")
        end_idx = text.rfind("}")
        if start_idx != -1 and end_idx != -1:
            text = text[start_idx:end_idx+1]
        
        diag_json = json.loads(text)
        required_keys = ["primary_diagnosis", "matching_symptoms", "immediate_precautions", "vet_urgency"]
        t1_pass = all(k in diag_json for k in required_keys)
        
        formatted = format_response_for_farmer(diag_json)
        print(" Formatted Output:")
        print(formatted)
        test_results["Test 1"] = "PASS" if t1_pass else "FAIL"
    except Exception as e:
        print(f" Test 1 Parse Error: {e}")
        print(f" Full text was: {response['text']}")
        test_results["Test 1"] = "FAIL"

    # --- Test 2: Confidence Update ---
    print("\n[Test 2] Confidence Update (Low -> High)...")
    s2_low = "animal seems sick"
    r2_low = retrieval.retrieve_all(mastitis_img, s2_low)
    r2_low = reranker.rerank_all(s2_low, r2_low)
    
    top_low = r2_low["disease_candidates"][0]
    conf_low = compute_confidence(**extract_scores_from_retrieval(top_low, r2_low))
    route_low = route_by_confidence(conf_low)
    
    print(f" Initial confidence: {conf_low['percentage']}% | Action: {route_low['action']}")
    
    # Simulate follow-up
    enriched_symptoms = s2_low + ". Cow has swollen udder and milk has clots."
    r2_high = retrieval.retrieve_all(mastitis_img, enriched_symptoms)
    r2_high = reranker.rerank_all(enriched_symptoms, r2_high)
    
    top_high = r2_high["disease_candidates"][0]
    provided_high = [s.strip() for s in enriched_symptoms.replace(",", " ").split()]
    conf_high = compute_confidence(**extract_scores_from_retrieval(top_high, r2_high, provided_symptoms=provided_high))
    
    print(f" Enriched confidence: {conf_high['percentage']}%")
    test_results["Test 2"] = "PASS" if conf_high["percentage"] > conf_low["percentage"] else "FAIL"

    # --- Test 3: Gemini Fallback ---
    print("\n[Test 3] Gemini Fallback Routing...")
    routing_context = {"confidence_score": 0.35}
    # Force Gemini by context
    start = time.time()
    response_fallback = llm_router.generate("Tell me about cow health", routing_context=routing_context)
    duration_f = (time.time() - start) * 1000
    total_time += duration_f
    
    print(f" Routed to: {response_fallback.get('routed_to')}")
    test_results["Test 3"] = "PASS" if response_fallback.get("routed_to") == "gemini" else "FAIL"

    # --- Test 4: Memory Storage ---
    print("\n[Test 4] Memory Storage...")
    case_id = await memory.save_case({
        "user_id": "farmer_123",
        "animal_type": "cow",
        "symptoms_text": s1,
        "primary_diagnosis": "Mastitis",
        "confidence_score": 0.85
    })
    
    await memory.save_chat_message(case_id, "user", s1)
    await memory.save_chat_message(case_id, "assistant", "This looks like Mastitis.")
    
    history = await memory.get_case_history("farmer_123")
    chat = await memory.get_chat_history(case_id)
    
    t4_pass = len(history) > 0 and len(chat) == 2
    print(f" Cases for user: {len(history)} | Chat messages: {len(chat)}")
    test_results["Test 4"] = "PASS" if t4_pass else "FAIL"

    # --- Test 5: Full Session Simulation ---
    print("\n[Test 5] Full Session Simulation...")
    # T1
    res_t1 = retrieval.retrieve_all(mastitis_img, "my cow is sick")
    conf_t1 = compute_confidence(**extract_scores_from_retrieval(res_t1["disease_candidates"][0], res_t1, provided_symptoms=["sick"]))
    route_t1 = route_by_confidence(conf_t1)
    q1 = question_gen.get_questions(route_t1["action"])
    
    # T2
    ans_t2 = [{"question": q1[0], "answer": "Yes, udder is very swollen"}]
    s2 = "my cow is sick. udder is very swollen"
    res_t2 = retrieval.retrieve_all(mastitis_img, s2)
    
    # T3
    s3 = "my cow is sick. udder is very swollen and milk has clots"
    res_t3 = retrieval.retrieve_all(mastitis_img, s3)
    p3 = [s.strip().lower() for s in s3.replace(".", " ").replace(",", " ").split()]
    top_t3 = res_t3["disease_candidates"][0]
    scores_t3 = extract_scores_from_retrieval(top_t3, res_t3, provided_symptoms=p3)
    conf_t3 = compute_confidence(**scores_t3)
    
    print(f" T3 Scores: Image={scores_t3['image_similarity']:.2f}, Text={scores_t3['text_similarity']:.2f}, Symptom={scores_t3['symptom_match']:.2f}")
    print(f" Progression: {conf_t1['percentage']}% -> ??? -> {conf_t3['percentage']}%")
    test_results["Test 5"] = "PASS" if conf_t3["percentage"] > 60 else "FAIL"

    # Final Report
    print("\n+---------------------------------------------+")
    print("|         LLM Pipeline Test Report            |")
    print("+--------------------------+------------------+")
    print(f"| Test 1 Diagnosis JSON    | {test_results['Test 1']:<16} |")
    print(f"| Test 2 Confidence update | {test_results['Test 2']:<16} |")
    print(f"| Test 3 Gemini fallback   | {test_results['Test 3']:<16} |")
    print(f"| Test 4 Memory storage    | {test_results['Test 4']:<16} |")
    print(f"| Test 5 Full session      | {test_results['Test 5']:<16} |")
    print("+--------------------------+------------------+")
    print(f"| Avg LLM response time    | {total_time/2:<14.2f}ms |")
    print(f"| Primary model used       | {llm_router.route({}):<16} |")
    stats = llm_router.get_routing_stats()
    print(f"| Fallbacks triggered      | {stats['fallback_triggers']:<16} |")
    print("+--------------------------+------------------+")
    ready = "YES" if all(v == "PASS" for v in test_results.values()) else "NO"
    print(f"LLM pipeline ready for API: {ready}")

if __name__ == "__main__":
    asyncio.run(main())
