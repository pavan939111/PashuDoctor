import requests
import os
import json
import time

API_URL = "http://localhost:8000"

def run_demo_case(name, image_path, symptoms, animal="cow"):
    print(f"\n>>> Running Demo Case: {name}")
    print(f"Symptoms: {symptoms}")
    
    if not os.path.exists(image_path):
        print(f"Error: Image not found at {image_path}")
        return

    start_time = time.time()
    
    try:
        with open(image_path, "rb") as f:
            files = {"image": (os.path.basename(image_path), f, "image/jpeg")}
            data = {
                "user_id": "demo_farmer_01",
                "symptom_text": symptoms,
                "animal_type": animal,
                "language": "english"
            }
            
            response = requests.post(f"{API_URL}/analyze/image", data=data, files=files)
            
        res = response.json()
        duration = time.time() - start_time
        
        if res.get("success"):
            diag = res["diagnosis"]
            print(f"Success! (Time: {duration:.2f}s)")
            print(f"Primary Diagnosis: {diag['primary_diagnosis']}")
            print(f"Confidence: {res['confidence']['percentage']}")
            print(f"Advice: {diag['farmer_advice'][:100]}...")
        else:
            print(f"Failed: {res.get('error')}")
            
    except Exception as e:
        print(f"Error connecting to API: {e}")

if __name__ == "__main__":
    print("=== PashuDoctor Live Demo Runner ===")
    
    # 1. Mastitis Case
    run_demo_case(
        "Mastitis Detection", 
        r"C:\Users\mahip\.cache\kagglehub\datasets\sivaprathishsiva\mastitis-disease-detection\versions\1\Data\mastitis\Picture40-400x284.jpg",
        "swollen udder, yellow clots in milk, fever"
    )
    
    # 2. Healthy Case
    run_demo_case(
        "Healthy Animal Check",
        r"C:\Users\mahip\.cache\kagglehub\datasets\sivaprathishsiva\mastitis-disease-detection\versions\1\Data\23.jpeg",
        "animal looks normal, no symptoms"
    )
