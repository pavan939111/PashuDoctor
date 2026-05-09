import os
import sys
import json
import numpy as np

# Add backend to sys.path
sys.path.append(os.path.join(os.getcwd(), "backend"))

try:
    from app.services.retrieval_service import ChromaDBManager, BM25IndexManager
except ImportError:
    print("Error: Could not import backend services. Please ensure dependencies are installed.")
    sys.exit(1)

def demo_setup():
    print("Starting PashuDoctor Demo Setup (Minimal Mode)...")
    
    # 1. Ensure directories exist
    os.makedirs("data/chroma_db", exist_ok=True)
    os.makedirs("data/knowledge_base", exist_ok=True)
    os.makedirs("data/processed", exist_ok=True)
    
    # 2. Create sample disease descriptions
    descriptions = {
        "foot_and_mouth": "Blisters in mouth and feet, drooling.",
        "mastitis": "Swollen udder, clots in milk.",
        "lumpy_skin_disease": "Lumps on skin, fever.",
        "blackquarter": "Swelling in legs, crackling sound.",
        "hemorrhagic_septicemia": "Throat swelling, difficulty breathing.",
        "ppr": "Sores in mouth, diarrhea in goats."
    }
    
    with open("data/knowledge_base/disease_descriptions.json", "w") as f:
        json.dump(descriptions, f, indent=4)
        
    # 3. Create minimal chunks.jsonl
    chunks = []
    for disease, desc in descriptions.items():
        chunks.append({
            "chunk_id": f"demo_{disease}",
            "text": desc,
            "source": "demo_source",
            "disease_tags": [disease],
            "animal_tags": ["cow", "buffalo", "goat", "sheep"]
        })
        
    with open("data/knowledge_base/chunks.jsonl", "w") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk) + "\n")
            
    # 4. Initialize Chroma and add sample records
    print("Populating ChromaDB with sample data...")
    from app.dependencies import initialise_services, get_image_service, get_text_service
    import asyncio
    
    # We need to run the async initialization
    async def init_and_embed():
        await initialise_services()
        image_service = get_image_service()
        text_service = get_text_service()
        chroma = ChromaDBManager()
        chroma.delete_and_rebuild("REBUILD")
        
        animals = ["cow", "buffalo", "goat", "sheep"]
        print("Generating real embeddings for 50 demo cases...")
        for i in range(50):
            disease = list(descriptions.keys())[i % len(descriptions)]
            animal = animals[i % len(animals)]
            desc = descriptions[disease]
            
            # Use text embedding as a proxy for image embedding in this demo
            # or just a zero vector if we don't have images, but random is bad.
            # Actually, let's use the text embedding of the description.
            # CLIP image and text embeddings are in the same space (sort of), 
            # but here we'll just use the text embedding to ensure BM25 and Dense both have something to bite on.
            
            # Generate a "fake" image embedding by using the text embedding of the disease name
            # CLIP can encode text too.
            import torch
            import clip
            with torch.no_grad():
                text_tokens = clip.tokenize([f"a photo of a {animal} with {disease}"]).to(image_service.device)
                emb = image_service.model.encode_text(text_tokens).cpu().numpy().flatten()
                # Normalize
                emb = emb / np.linalg.norm(emb)

            meta = {
                "animal": animal,
                "disease": disease,
                "body_part": "unknown",
                "severity": "unknown",
                "source": "demo",
                "split": "train",
                "description": f"A {animal} showing symptoms of {disease}: {desc}"
            }
            chroma.add_disease_image(f"demo_{i}", emb, meta)
            
        # Add Knowledge Chunks
        print("Adding knowledge chunks...")
        for disease, desc in descriptions.items():
            text = f"{disease.replace('_', ' ').title()}: {desc}"
            emb = text_service.get_text_embedding(text)
            meta = {
                "source": "demo_kb",
                "disease_tags": [disease],
                "animal_tags": ["cow", "buffalo", "goat", "sheep"]
            }
            chroma.add_knowledge_chunk(f"kb_{disease}", emb, meta, text)
            
        return chroma

    chroma = asyncio.run(init_and_embed())
        
    # 5. Build BM25 Index
    print("Building BM25 indexes...")
    bm25 = BM25IndexManager(chroma)
    bm25.rebuild_indexes()
    
    print("\nDemo Setup Complete! You can now run the app.")
    print("Run command: make run (for backend) and make frontend (for UI)")

if __name__ == "__main__":
    demo_setup()
