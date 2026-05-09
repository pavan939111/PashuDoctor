BREED_RISK_MAP = {
    # Cattle
    "Jersey":    {"high_risk": ["mastitis", "milk_fever"],
                  "region": "all India"},
    "Holstein":  {"high_risk": ["mastitis", "milk_fever"],
                  "region": "Punjab, Haryana"},
    "Sahiwal":   {"high_risk": ["tick_fever", "fmd"],
                  "region": "Punjab, Rajasthan"},
    "Gir":       {"high_risk": ["fmd", "hs"],
                  "region": "Gujarat"},
    "Tharparkar":{"high_risk": ["fmd", "hs"],
                  "region": "Rajasthan"},
    # Buffalo
    "Murrah":    {"high_risk": ["mastitis", "heat_stress"],
                  "region": "Haryana, Punjab"},
    "Surti":     {"high_risk": ["fmd", "mastitis"],
                  "region": "Gujarat"},
    "Nili-Ravi": {"high_risk": ["fmd", "hs"],
                  "region": "Punjab"},
    # Goat
    "Beetal":    {"high_risk": ["ppr", "fmd"],
                  "region": "Punjab"},
    "Black Bengal":{"high_risk": ["ppr"],
                   "region": "West Bengal"},
    # Sheep
    "Merino":    {"high_risk": ["fmd", "lsd"],
                  "region": "South India"},
}

def get_breed_confidence_boost(breed: str, top_disease: str) -> float:
    """Returns a confidence boost if the disease is high-risk for the breed"""
    if not breed or breed == "Unknown":
        return 0.0
    
    # Normalize
    breed_key = breed.title()
    disease_key = top_disease.lower().replace(" ", "_")
    
    if breed_key in BREED_RISK_MAP:
        if disease_key in BREED_RISK_MAP[breed_key]["high_risk"]:
            return 0.08  # boost confidence by 8%
    return 0.0

def get_breed_context(breed: str) -> str:
    """Returns a clinical context string for the LLM prompt"""
    if not breed or breed == "Unknown" or breed not in BREED_RISK_MAP:
        return ""
    
    risk_info = BREED_RISK_MAP[breed]
    diseases = ", ".join(risk_info["high_risk"])
    region = risk_info["region"]
    
    return f"Note: {breed} animals have elevated risk for {diseases} in {region}. Factor this into diagnosis."

def get_supported_breeds():
    return ["Unknown"] + list(BREED_RISK_MAP.keys()) + ["Other"]
