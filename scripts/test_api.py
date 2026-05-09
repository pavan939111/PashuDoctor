import asyncio
import httpx
import os
import time
import json

BASE_URL = "http://localhost:8000"
# Find a test image dynamically or use the known one
TEST_IMAGE = r"C:\Users\mahip\OneDrive\Desktop\Animal_health_care\pashudoctor\data\raw\fmd_cattle_local\FMD_Cattle\0\Cows head, open mouth 1.jpeg"

async def test_api():
    results = {}
    times = []
    case_id = None
    
    print("Starting API Integration Test...")
    print(f"Target URL: {BASE_URL}")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Test 1: Health check
        print("\n[Test 1] Health Check...")
        start = time.time()
        try:
            res = await client.get(f"{BASE_URL}/history/health")
            duration = (time.time() - start) * 1000
            times.append(duration)
            if res.status_code == 200:
                data = res.json()
                print(f" Status: {data['status']} ({duration:.2f}ms)")
                for svc, ok in data["services"].items():
                    print(f"  - {svc}: {'[OK]' if ok else '[FAIL]'}")
                results["Health check"] = "PASS"
            else:
                print(f" Failed: {res.status_code}")
                results["Health check"] = "FAIL"
        except Exception as e:
            print(f" Error: {e}")
            results["Health check"] = "FAIL"

        # Test 2: Analyze image
        print("\n[Test 2] Analyze Image...")
        if os.path.exists(TEST_IMAGE):
            start = time.time()
            try:
                with open(TEST_IMAGE, "rb") as f:
                    files = {"image": ("test.jpg", f, "image/jpeg")}
                    data = {
                        "user_id": "test_user_001",
                        "symptom_text": "cow with swollen udder reduced milk",
                        "animal_type": "cow",
                        "language": "english"
                    }
                    res = await client.post(f"{BASE_URL}/analyze/image", files=files, data=data)
                    duration = (time.time() - start) * 1000
                    times.append(duration)
                    if res.status_code == 200:
                        resp_data = res.json()
                        case_id = resp_data["case_id"]
                        print(f" Success! Case ID: {case_id} ({duration:.2f}ms)")
                        print(f" Animal: {resp_data['animal_detection']['animal']}")
                        print(f" Confidence: {resp_data['confidence']['percentage']}%")
                        results["Analyze image"] = "PASS"
                    else:
                        print(f" Failed ({res.status_code}): {res.text}")
                        results["Analyze image"] = "FAIL"
            except Exception as e:
                print(f" Error: {e}")
                results["Analyze image"] = "FAIL"
        else:
            print(f" Test image not found at {TEST_IMAGE}")
            results["Analyze image"] = "FAIL"

        # Test 3: Text only analysis
        print("\n[Test 3] Text Only Analysis...")
        start = time.time()
        try:
            payload = {
                "user_id": "test_user_001",
                "symptom_text": "buffalo with high fever neck swelling difficulty breathing monsoon season",
                "animal_type": "buffalo",
                "language": "english"
            }
            res = await client.post(f"{BASE_URL}/analyze/text-only", json=payload)
            duration = (time.time() - start) * 1000
            times.append(duration)
            if res.status_code == 200:
                resp_data = res.json()
                print(f" Success! Top candidate: {resp_data['top_candidates'][0]['disease']} ({duration:.2f}ms)")
                if resp_data.get("diagnosis"):
                    print(f" Diagnosis: {resp_data['diagnosis']['primary_diagnosis']}")
                results["Text only analysis"] = "PASS"
            else:
                print(f" Failed: {res.status_code}")
                results["Text only analysis"] = "FAIL"
        except Exception as e:
            print(f" Error: {e}")
            results["Text only analysis"] = "FAIL"

        # Test 4: Chat follow-up
        if case_id:
            print("\n[Test 4] Chat Follow-up...")
            start = time.time()
            try:
                payload = {
                    "case_id": case_id,
                    "user_id": "test_user_001",
                    "message": "Yes the udder is very hot and swollen, milk has blood clots"
                }
                res = await client.post(f"{BASE_URL}/chat/message", json=payload)
                duration = (time.time() - start) * 1000
                times.append(duration)
                if res.status_code == 200:
                    resp_data = res.json()
                    print(f" Assistant: {resp_data['response'][:100]}... ({duration:.2f}ms)")
                    print(f" Diagnosis Updated: {resp_data['diagnosis_updated']}")
                    results["Chat follow-up"] = "PASS"
                else:
                    print(f" Failed: {res.status_code}")
                    results["Chat follow-up"] = "FAIL"
            except Exception as e:
                print(f" Error: {e}")
                results["Chat follow-up"] = "FAIL"
        else:
            results["Chat follow-up"] = "SKIP"

        # Test 5: Answer questions
        if case_id:
            print("\n[Test 5] Answer Questions...")
            start = time.time()
            try:
                payload = {
                    "case_id": case_id,
                    "user_id": "test_user_001",
                    "question_answers": [
                        {"question": "Is udder swollen?", "answer": "Yes very swollen and hot"},
                        {"question": "Has milk changed?", "answer": "Yes very less milk with clots"}
                    ],
                    "symptom_text": "cow with swollen udder"
                }
                res = await client.post(f"{BASE_URL}/chat/answer-questions", json=payload)
                duration = (time.time() - start) * 1000
                times.append(duration)
                if res.status_code == 200:
                    resp_data = res.json()
                    if resp_data.get("diagnosis"):
                        print(f" Updated Diagnosis: {resp_data['diagnosis']['primary_diagnosis']} ({duration:.2f}ms)")
                    else:
                        print(" Confidence still low, no diagnosis yet.")
                    results["Answer questions"] = "PASS"
                else:
                    print(f" Failed: {res.status_code}")
                    results["Answer questions"] = "FAIL"
            except Exception as e:
                print(f" Error: {e}")
                results["Answer questions"] = "FAIL"
        else:
            results["Answer questions"] = "SKIP"

        # Test 6: History
        print("\n[Test 6] History...")
        start = time.time()
        try:
            res = await client.get(f"{BASE_URL}/history/test_user_001")
            duration = (time.time() - start) * 1000
            times.append(duration)
            if res.status_code == 200:
                data = res.json()
                print(f" Found {data['total']} records for user test_user_001 ({duration:.2f}ms)")
                results["History"] = "PASS"
            else:
                print(f" Failed: {res.status_code}")
                results["History"] = "FAIL"
        except Exception as e:
            results["History"] = "FAIL"

        # Test 7: Feedback
        if case_id:
            print("\n[Test 7] Feedback...")
            start = time.time()
            try:
                payload = {
                    "case_id": case_id,
                    "feedback_correct": True,
                    "farmer_note": "The AI was very helpful, vet confirmed mastitis."
                }
                res = await client.post(f"{BASE_URL}/history/feedback", json=payload)
                duration = (time.time() - start) * 1000
                times.append(duration)
                if res.status_code == 200:
                    print(f" Feedback submitted successfully ({duration:.2f}ms)")
                    results["Feedback"] = "PASS"
                else:
                    print(f" Failed: {res.status_code}")
                    results["Feedback"] = "FAIL"
            except Exception as e:
                results["Feedback"] = "FAIL"
        else:
            results["Feedback"] = "SKIP"

    # Final Report
    avg_time = sum(times) / len(times) if times else 0
    all_ok = all(v in ["PASS", "SKIP"] for v in results.values())
    
    print("\n" + "="*45)
    print("          API Test Report")
    print("-" * 45)
    for test, res in results.items():
        print(f" {test:<24} | {res:<16}")
    print("-" * 45)
    print(f" Avg response time        | {avg_time:7.2f}ms")
    print(f" All endpoints working    | {'YES' if all_ok else 'NO'}")
    print("="*45)
    
    print(f"\nBackend ready for frontend: {'YES' if all_ok else 'NO'}")

if __name__ == "__main__":
    try:
        asyncio.run(test_api())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Test runner failed: {e}")
