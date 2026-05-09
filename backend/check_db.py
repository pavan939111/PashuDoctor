import chromadb
client = chromadb.PersistentClient(path='data/chroma_db')
try:
    c1 = client.get_collection("livestock_diseases")
    print(f"Disease chunks: {c1.count()}")
except Exception as e:
    print(f"Disease collection error: {e}")
try:
    c2 = client.get_collection("knowledge_base")
    print(f"Knowledge chunks: {c2.count()}")
except Exception as e:
    print(f"Knowledge collection error: {e}")
