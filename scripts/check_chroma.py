import os
import sys
import json

# Add backend to sys.path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.services.retrieval_service import ChromaDBManager

def main():
    c = ChromaDBManager()
    data = c.disease_collection.get(include=["metadatas"])
    mastitis = [m for m in data["metadatas"] if m["disease"] == "mastitis"]
    print(f"Total records in Chroma: {len(data['metadatas'])}")
    print(f"Mastitis count: {len(mastitis)}")
    if mastitis:
        print(f"First 5 Mastitis animals: {[m.get('animal') for m in mastitis[:5]]}")
    else:
        print("No Mastitis found!")

if __name__ == "__main__":
    main()
