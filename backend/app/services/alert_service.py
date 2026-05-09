from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# Static database of known outbreaks (Manually curated for demo purposes)
STATIC_ALERT_DB = {
    "foot_and_mouth": [
        {"state": "Maharashtra", "district": "Pune", "date": "2026-05-01", "severity": "high"},
        {"state": "Uttar Pradesh", "district": "Lucknow", "date": "2026-04-15", "severity": "medium"},
        {"state": "Telangana", "district": "Hyderabad", "date": "2026-05-05", "severity": "high"},
    ],
    "lumpy_skin_disease": [
        {"state": "Rajasthan", "district": "Jaipur", "date": "2026-05-02", "severity": "high"},
        {"state": "Punjab", "district": "Ludhiana", "date": "2026-04-20", "severity": "high"},
    ],
    "ppr": [
        {"state": "Tamil Nadu", "district": "Madurai", "date": "2026-05-03", "severity": "medium"},
        {"state": "Karnataka", "district": "Mysore", "date": "2026-04-25", "severity": "low"},
    ],
    "hemorrhagic_septicemia": [
        {"state": "West Bengal", "district": "Hooghly", "date": "2026-05-04", "severity": "high"},
    ]
}

def get_active_alerts(state: str, disease: Optional[str] = None) -> List[Dict[str, Any]]:
    """Returns active alerts for a state within the last 60 days"""
    active_alerts = []
    sixty_days_ago = datetime.now() - timedelta(days=60)
    
    for disease_key, alerts in STATIC_ALERT_DB.items():
        # If disease filter is provided, skip others
        if disease and disease != disease_key:
            continue
            
        for alert in alerts:
            if alert["state"].lower() == state.lower():
                alert_date = datetime.strptime(alert["date"], "%Y-%m-%d")
                if alert_date >= sixty_days_ago:
                    active_alerts.append({
                        "disease": disease_key.replace("_", " ").title(),
                        "district": alert["district"],
                        "date": alert["date"],
                        "severity": alert["severity"]
                    })
    
    # Sort by date (newest first)
    active_alerts.sort(key=lambda x: x["date"], reverse=True)
    return active_alerts
