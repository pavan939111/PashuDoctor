import os
import json
import uuid
import chromadb
from tqdm import tqdm
from PIL import Image
import sys

# Add backend to path to import services
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))
from app.services.image_service import ImageService
from app.config import get_settings

settings = get_settings()

def main():
    # Initialize services
    image_service = ImageService()
    
    # Initialize ChromaDB
    client = chromadb.PersistentClient(path=settings.CHROMA_PATH)
    collection = client.get_or_create_collection(name=settings.CHROMA_COLLECTION)
    
    # Load download paths
    paths_file = os.path.join("pashudoctor", "data", "download_paths.json")
    if not os.path.exists(paths_file):
        # Try local data/ too if running from pashudoctor/
        paths_file = os.path.join("data", "download_paths.json")
        if not os.path.exists(paths_file):
            print(f"FAILED: {paths_file} not found. Run download scripts first.")
            return
        
    with open(paths_file, "r") as f:
        download_paths = json.load(f)
        
    # We will process both base animal folders and disease datasets
    # Mapping for base animals
    base_animals = ["cow", "goat", "sheep", "buffalo"]
    
    for animal in base_animals:
        if animal in download_paths:
            path = download_paths[animal]
            print(f" Processing base animal folder: {animal} -> {path}")
            embed_directory(collection, image_service, path, {"animal": animal, "source": "base_dataset", "disease": "healthy"})

    # Process FMD Cattle Local (extracted from ZIP)
    if "fmd_cattle_local" in download_paths:
        path = download_paths["fmd_cattle_local"]
        print(f" Processing local FMD folder: {path}")
        # Assuming FMD folder has subfolders or just images
        embed_directory(collection, image_service, path, {"animal": "cow", "source": "local_zip", "disease": "fmd"})

    # Process Kaggle/Roboflow datasets if they have labels
    # (For now focusing on the confirmed ones)
    
    print(f" Ingestion complete. Total items in collection: {collection.count()}")

def embed_directory(collection, image_service, directory, metadata_base):
    """Recursively find images and add to collection."""
    valid_extensions = (".jpg", ".jpeg", ".png", ".webp")
    
    # Count total files first for progress bar
    total_files = 0
    for root, _, files in os.walk(directory):
        total_files += len([f for f in files if f.lower().endswith(valid_extensions)])
        
    if total_files == 0:
        print(f" No images found in {directory}")
        return

    with tqdm(total=total_files, desc=f"Embedding {metadata_base['animal']}") as pbar:
        for root, _, files in os.walk(directory):
            for file in files:
                if file.lower().endswith(valid_extensions):
                    file_path = os.path.join(root, file)
                    try:
                        # Extract embedding
                        embedding = image_service.get_clip_embedding(file_path)
                        
                        # Prepare metadata
                        metadata = metadata_base.copy()
                        metadata["filename"] = file
                        metadata["original_path"] = file_path
                        
                        # Add to Chroma
                        collection.add(
                            ids=[str(uuid.uuid4())],
                            embeddings=[embedding],
                            metadatas=[metadata],
                            documents=[f"{metadata['animal']} {metadata['disease']}"]
                        )
                    except Exception as e:
                        # print(f" Failed to process {file_path}: {e}")
                        pass
                    pbar.update(1)

if __name__ == "__main__":
    main()
