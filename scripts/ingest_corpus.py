import os
import sys
import json
import numpy as np
import asyncio
import torch
import clip

# Add backend to sys.path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.dependencies import initialise_services, get_image_service, get_text_service
from app.services.retrieval_service import ChromaDBManager, BM25IndexManager

async def ingest_semantic_corpus():
    print("--- PashuDoctor Semantic Ingestion Pipeline ---")
    
    # 1. Initialize Services
    await initialise_services()
    image_service = get_image_service()
    text_service = get_text_service()
    chroma = ChromaDBManager()
    
    # Wipe old random data
    print("Wiping existing collections for clean rebuild...")
    chroma.delete_and_rebuild("REBUILD")
    
    # 2. Load Manifest
    manifest_path = "data/knowledge_base/disease_manifest.json"
    if not os.path.exists(manifest_path):
        print(f"❌ Error: Manifest not found at {manifest_path}")
        return
        
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
        
    diseases = manifest.get("diseases", [])
    print(f"Loaded {len(diseases)} diseases from manifest.")
    
    # 3. Process each disease
    for disease in diseases:
        d_name = disease["name"]
        d_id = disease["id"]
        
        print(f"\nProcessing: {d_name}...")
        
        # a. Generate Knowledge Chunk for RAG
        # We combine description, symptoms, and treatment into a rich text chunk
        full_text = (
            f"Disease: {d_name}\n"
            f"Description: {disease['description']}\n"
            f"Symptoms: {', '.join(disease['symptoms'])}\n"
            f"Affected Animals: {', '.join(disease['animal_types'])}\n"
            f"Affected Body Parts: {', '.join(disease['body_parts'])}\n"
            f"Severity: {disease['severity']}\n"
            f"Treatment: {'. '.join(disease['treatment_guidance'])}\n"
            f"Prevention: {disease['preventive_care']}\n"
            f"Source: {disease['source']}"
        )
        
        text_emb = text_service.get_text_embedding(full_text)
        kb_meta = {
            "source": disease["source"],
            "disease_tags": [d_id, d_name.lower().replace(" ", "_")],
            "animal_tags": disease["animal_types"],
            "severity": disease["severity"]
        }
        chroma.add_knowledge_chunk(f"kb_{d_id}", text_emb, kb_meta, full_text)
        
        # b. Generate Multi-Modal Reference Samples
        # For a production system, we'd embed actual verified photos here.
        # Since we are rebuilding, we will generate "Anchor" embeddings using CLIP's text encoder.
        # These anchors represent the 'semantic center' of how CLIP sees these diseases.
        
        for animal in disease["animal_types"]:
            # We generate 3 anchors per animal: General, Close-up, and Symptom-specific
            anchors = [
                f"a photo of a {animal} with {d_name}",
                f"clinical closeup of {disease['symptoms'][0]} in a {animal}",
                f"veterinary photo of {d_name} affecting {disease['body_parts'][0]}"
            ]
            
            for i, anchor_text in enumerate(anchors):
                with torch.no_grad():
                    tokens = clip.tokenize([anchor_text]).to(image_service.device)
                    # Use CLIP text encoder to get a vector in the SAME space as CLIP image embeddings
                    image_emb = image_service.model.encode_text(tokens).cpu().numpy().flatten()
                    image_emb = image_emb / np.linalg.norm(image_emb) # Normalize
                
                img_meta = {
                    "animal": animal,
                    "disease": d_name.lower().replace(" ", "_"),
                    "disease_label": d_name,
                    "body_part": disease["body_parts"][0],
                    "severity": disease["severity"].lower(),
                    "source": "clinical_anchor",
                    "description": anchor_text,
                    "symptoms": disease["symptoms"], # Include full symptom list in metadata for BM25
                    "split": "train"
                }
                chroma.add_disease_image(f"anchor_{d_id}_{animal}_{i}", image_emb, img_meta)

    # 4. Build BM25 Index
    print("\n--- Rebuilding BM25 Search Indexes ---")
    bm25 = BM25IndexManager(chroma)
    bm25.rebuild_indexes()
    
    # 5. Validation
    stats = chroma.get_collection_stats()
    print("\nIngestion Complete!")
    print(f"Total Disease Anchors: {stats['total']}")
    print(f"Knowledge Chunks: {chroma.knowledge_collection.count()}")
    print(f"BM25 Indexes: OK")

if __name__ == "__main__":
    asyncio.run(ingest_semantic_corpus())
