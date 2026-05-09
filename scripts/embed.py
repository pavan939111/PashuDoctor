import os
import sys
import json
import argparse
import pandas as pd
import numpy as np
from tqdm import tqdm

# Add backend to sys.path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.services.image_service import ImageService
from app.services.text_service import TextEmbeddingService
from app.services.retrieval_service import ChromaDBManager, BM25IndexManager

# Configuration
MANIFEST_PATH = os.path.join("data", "processed", "test_manifest.csv")
CHUNKS_PATH = os.path.join("data", "knowledge_base", "chunks.jsonl")
SKIPPED_LOG = os.path.join("data", "processed", "skipped.csv")

def main():
    parser = argparse.ArgumentParser(description="End-to-end ChromaDB Ingestion")
    parser.add_argument("--skip-images", action="store_true", help="Only ingest knowledge chunks")
    parser.add_argument("--skip-knowledge", action="store_true", help="Only ingest images")
    parser.add_argument("--rebuild", action="store_true", help="Delete and recreate collections first")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size for image embedding")
    args = parser.parse_args()

    # Initialize Services
    image_service = ImageService()
    text_service = TextEmbeddingService()
    chroma = ChromaDBManager()

    if args.rebuild:
        print("Rebuilding collections...")
        chroma.delete_and_rebuild("REBUILD")

    skipped_records = []

    # Phase A: Embed and Ingest Disease Images
    if not args.skip_images:
        if not os.path.exists(MANIFEST_PATH):
            print(f"FAILED: {MANIFEST_PATH} not found.")
        else:
            df = pd.read_csv(MANIFEST_PATH)
            df = df.head(1000) # Limit for fast test indexing
            print(f"Phase A: Processing {len(df)} images...")
            
            for i in tqdm(range(0, len(df), args.batch_size), desc="Ingesting Images"):
                batch_df = df.iloc[i : i + args.batch_size]
                batch_paths = batch_df["image_path"].tolist()
                
                # Batch embed images
                batch_embeddings = image_service.process_batch(batch_paths, batch_size=args.batch_size)
                
                for j, (index, row) in enumerate(batch_df.iterrows()):
                    img_path = row["image_path"]
                    
                    # Get precomputed embedding
                    image_emb = batch_embeddings[j]
                    
                    # 3. Get clinical text description embedding
                    disease_text = text_service.get_disease_text(
                        disease=row["disease_label"], 
                        animal=row["animal_type"]
                    )
                    text_emb = text_service.get_text_embedding(disease_text)
                    
                    # 4. Multimodal combination (0.6 Visual + 0.4 Text)
                    text_emb_512 = np.pad(text_emb, (0, 512 - 384), 'constant')
                    combined = 0.6 * image_emb + 0.4 * text_emb_512
                    combined = combined / np.linalg.norm(combined)
                    
                    # 5. Build Metadata
                    metadata = {
                        "animal": str(row["animal_type"]),
                        "disease": str(row["disease_label"]),
                        "description": disease_text,
                        "body_part": "unknown", 
                        "severity": "unknown",
                        "source": str(row["dataset_source"]),
                        "split": str(row["split"])
                    }
                    
                    # 6. Add to Chroma
                    chroma.add_disease_image(str(row["image_id"]), combined, metadata)

            # Save skipped
            if skipped_records:
                pd.DataFrame(skipped_records).to_csv(SKIPPED_LOG, index=False)
                print(f"Logged {len(skipped_records)} skipped images to {SKIPPED_LOG}")

    # Phase B: Embed and Ingest Knowledge Chunks
    if not args.skip_knowledge:
        if not os.path.exists(CHUNKS_PATH):
            print(f"FAILED: {CHUNKS_PATH} not found.")
        else:
            print(f"Phase B: Ingesting knowledge chunks...")
            with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
                chunks = [json.loads(line) for line in f]
            
            for chunk in tqdm(chunks, desc="Ingesting Knowledge"):
                # Get embedding
                embedding = text_service.embed_knowledge_chunk(chunk)
                
                # Metadata
                metadata = {
                    "source": chunk["source"],
                    "disease_tags": ", ".join(chunk["disease_tags"]),
                    "animal_tags": ", ".join(chunk["animal_tags"])
                }
                
                # Add
                chroma.add_knowledge_chunk(
                    chunk["chunk_id"], 
                    embedding, 
                    metadata, 
                    chunk["text"]
                )

    # Final Validation
    print("\nFinalizing Ingestion Stats...")
    stats = chroma.get_collection_stats()
    
    print("\nRebuilding BM25 Indexes...")
    bm25 = BM25IndexManager(chroma)
    bm25.rebuild_indexes()
    
    # We need to get knowledge count separately as stats only does disease
    k_count = chroma.knowledge_collection.count()
    
    print("\n┌─────────────────────────────────────────────┐")
    print("│         ChromaDB Ingestion Complete         │")
    print("├──────────────────────────┬──────────────────┤")
    print(f"│ Disease images ingested  │ {stats['total']:<16} │")
    print(f"│ Knowledge chunks ingested│ {k_count:<16} │")
    print(f"│ Skipped (quality)        │ {len(skipped_records):<16} │")
    print("├──────────────────────────┼──────────────────┤")
    print(f"│ cow                      │ {stats['by_animal'].get('cow', 0):<16} │")
    print(f"│ buffalo                  │ {stats['by_animal'].get('buffalo', 0):<16} │")
    print(f"│ goat                     │ {stats['by_animal'].get('goat', 0):<16} │")
    print(f"│ sheep                    │ {stats['by_animal'].get('sheep', 0):<16} │")
    print("├──────────────────────────┼──────────────────┤")
    print(f"│ foot_and_mouth           │ {stats['by_disease'].get('foot_and_mouth', 0):<16} │")
    print(f"│ mastitis                 │ {stats['by_disease'].get('mastitis', 0):<16} │")
    print(f"│ lumpy_skin_disease       │ {stats['by_disease'].get('lumpy_skin_disease', 0):<16} │")
    print(f"│ blackquarter             │ {stats['by_disease'].get('blackquarter', 0):<16} │")
    print(f"│ hemorrhagic_septicemia   │ {stats['by_disease'].get('hemorrhagic_septicemia', 0):<16} │")
    print(f"│ ppr                      │ {stats['by_disease'].get('ppr', 0):<16} │")
    print(f"│ healthy                  │ {stats['by_disease'].get('healthy', 0):<16} │")
    print("└──────────────────────────┴──────────────────┘")

if __name__ == "__main__":
    main()
