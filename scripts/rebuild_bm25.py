import os
import sys

# Add backend to sys.path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.services.retrieval_service import ChromaDBManager, BM25IndexManager

def main():
    print("Rebuilding BM25 Indexes...")
    chroma = ChromaDBManager()
    bm25 = BM25IndexManager(chroma)
    bm25.rebuild_indexes()
    print("Done!")

if __name__ == "__main__":
    main()
