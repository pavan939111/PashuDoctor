import httpx
import json
import os
import time
from pathlib import Path

BASE = "http://localhost:8000"
TEST_USER = "integration_test_user_001"

def check_res(r):
    if r.status_code != 200:
        raise Exception(f"Status {r.status_code}: {r.text[:200]}")
    data = r.json()
    if data.get("success") == False:
        raise Exception(f"API Error: {data.get('error')}")
    return data

def test_health():
    print("\n=== Health Check ===")
    r = httpx.get(f"{BASE}/history/health", timeout=10)
    data = check_res(r)
    print("PASS: Health check")
    return data

def test_analyze_text():
    print("\n=== Analyze Text Only ===")
    payload = {
        "user_id": TEST_USER,
        "symptom_text": "My cow has swollen udder, reduced milk production, udder is hot and painful",
        "animal_type": "cow",
        "language": "english"
    }
    r = httpx.post(f"{BASE}/analyze/text-only", json=payload, timeout=120)
    data = check_res(r)
    print(f"  Case ID: {data.get('case_id')}")
    print("PASS: Text analysis endpoint")
    return data

def test_analyze_image():
    print("\n=== Analyze With Image ===")
    test_imgs = list(Path("data").rglob("*.jpg"))
    if not test_imgs: return {}
    img_path = test_imgs[0]
    with open(img_path, "rb") as f: img_bytes = f.read()
    files = {"images": (img_path.name, img_bytes, "image/jpeg")}
    data_form = {"user_id": TEST_USER, "symptom_text": "looks unwell", "language": "english"}
    r = httpx.post(f"{BASE}/analyze/image", files=files, data=data_form, timeout=180)
    data = check_res(r)
    print("PASS: Image analysis endpoint")
    return data

def test_history():
    print("\n=== History Endpoints ===")
    check_res(httpx.get(f"{BASE}/history/user/{TEST_USER}", timeout=30))
    check_res(httpx.get(f"{BASE}/history/user/{TEST_USER}/stats", timeout=30))
    print("PASS: History endpoints")

def test_feedback(case_id):
    print("\n=== Feedback Endpoint ===")
    payload = {"case_id": case_id, "feedback_correct": True, "farmer_note": "Confirmed"}
    check_res(httpx.post(f"{BASE}/history/feedback", json=payload, timeout=30))
    print("PASS: Feedback endpoint")

def test_emergency_intercept():
    print("\n=== Emergency Intercept ===")
    payload = {"user_id": TEST_USER, "symptom_text": "collapsed and not breathing", "language": "english"}
    check_res(httpx.post(f"{BASE}/analyze/text-only", json=payload, timeout=30))
    print("PASS: Emergency intercept")

def test_guardrails():
    print("\n=== Guardrail Tests ===")
    check_res(httpx.get(f"{BASE}/history/guardrails/audit", timeout=10))
    print("PASS: Guardrail tests")

def test_diseases_reference():
    print("\n=== Diseases Reference ===")
    check_res(httpx.get(f"{BASE}/history/diseases", timeout=10))
    print("PASS: Diseases reference endpoint")

def run_all():
    results = {}
    steps = [
        ("Health", test_health),
        ("Analyze Text", test_analyze_text),
        ("Analyze Image", test_analyze_image),
        ("History", test_history),
        ("Emergency", test_emergency_intercept),
        ("Guardrails", test_guardrails),
        ("Diseases", test_diseases_reference),
    ]
    case_id = None
    for name, func in steps:
        try:
            res = func()
            results[name] = "PASS"
            if name == "Analyze Text": case_id = res.get("case_id")
        except Exception as e:
            results[name] = f"FAIL: {e}"
    if case_id and case_id != "error":
        try: test_feedback(case_id); results["Feedback"] = "PASS"
        except Exception as e: results["Feedback"] = f"FAIL: {e}"
    print("\n" + "="*50)
    for name, status in results.items(): print(f"{name:<20}: {status}")
    print("="*50)

if __name__ == "__main__":
    run_all()
