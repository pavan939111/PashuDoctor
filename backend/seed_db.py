import chromadb
import uuid
import numpy as np
import torch
import clip
from PIL import Image

print("--- PashuDoctor Database Seeding Script (512-dim CLIP) ---")

# 1. Initialize
client = chromadb.PersistentClient(path='data/chroma_db')
device = "cpu" # Force CPU to save memory
model, preprocess = clip.load("ViT-B/32", device=device)

disease_col = client.get_or_create_collection(name="livestock_diseases", metadata={"hnsw:space": "cosine"})
knowledge_col = client.get_or_create_collection(name="knowledge_base", metadata={"hnsw:space": "cosine"})

def get_text_embedding(text):
    with torch.no_grad():
        # CLIP tokenize only supports up to 77 tokens
        tokens = clip.tokenize([text[:200]]).to(device) # Truncate for safety, though tokenize handles it
        features = model.encode_text(tokens)
        features /= features.norm(dim=-1, keepdim=True)
        return features.cpu().numpy().flatten().tolist()

def add_disease(name, animal, symptoms, body_part, severity, info):
    print(f"Adding disease: {name} ({animal})...")
    text = f"{name} in {animal}. Symptoms include {', '.join(symptoms)}. Affects {body_part}. Severity is {severity}. {info}"
    emb = get_text_embedding(text)
    
    disease_col.add(
        ids=[str(uuid.uuid4())],
        embeddings=[emb],
        metadatas=[{
            "disease": name.lower().replace(" ", "_"),
            "animal": animal.lower(),
            "body_part": body_part.lower(),
            "severity": severity.lower(),
            "type": "disease_record"
        }],
        documents=[text]
    )

def add_knowledge(title, text, animal_tags, disease_tags):
    print(f"Adding knowledge: {title}...")
    full_text = f"{title}\n\n{text}"
    emb = get_text_embedding(full_text)
    
    knowledge_col.add(
        ids=[str(uuid.uuid4())],
        embeddings=[emb],
        metadatas=[{
            "title": title,
            "animal_tags": ",".join(animal_tags),
            "disease_tags": ",".join(disease_tags),
            "source": "veterinary_manual"
        }],
        documents=[full_text]
    )

# 2. Seed Diseases
add_disease(
    "Bovine Mastitis", "cow", 
    ["swollen udder", "clots in milk", "blood in milk", "hot udder", "painful udder", "reduced milk yield"],
    "udder", "moderate",
    "Mastitis is an inflammation of the mammary gland and udder tissue. It is the most common disease in dairy cattle in India."
)

add_disease(
    "Foot and Mouth Disease", "cow", 
    ["blisters on mouth", "sores on hooves", "excessive drooling", "lameness", "limping", "high fever"],
    "mouth", "severe",
    "FMD is a highly contagious viral disease of livestock. It causes vesicles in the mouth and on the feet."
)

add_disease(
    "Lumpy Skin Disease", "cow", 
    ["skin nodules", "raised lumps", "fever", "loss of appetite", "nasal discharge"],
    "skin", "severe",
    "LSD is a viral disease in cattle transmitted by blood-feeding insects. It causes firm, circumscribed nodules on the skin."
)

add_disease(
    "PPR", "goat", 
    ["mouth ulcers", "sores in mouth", "diarrhoea", "nasal discharge", "fever", "respiratory distress"],
    "mouth", "severe",
    "PPR is a highly contagious viral disease affecting small ruminants. It is known as goat plague."
)

add_disease(
    "Hemorrhagic Septicemia", "buffalo", 
    ["throat swelling", "swollen neck", "breathing difficulty", "high fever", "frothing at mouth"],
    "throat", "emergency",
    "HS is a major bacterial disease of cattle and buffaloes, especially in tropical countries. It is often fatal."
)

# 3. Seed Knowledge Base
add_knowledge(
    "Managing Mastitis in Dairy Cattle",
    "Ensure complete milking and isolate affected animals. Clean udders with warm water and mild disinfectant. Maintain dry bedding to prevent further infection.",
    ["cow", "buffalo"], ["mastitis"]
)

add_knowledge(
    "Lumpy Skin Disease Prevention",
    "Isolate infected animals immediately. Use insect repellents and mosquito nets in the shed. Vaccination is the most effective way to control the spread.",
    ["cow", "buffalo"], ["lumpy_skin_disease"]
)

add_knowledge(
    "FMD First Aid and Care",
    "Wash mouth and feet with mild antiseptic (potassium permanganate). Apply boroglycerine to mouth sores. Provide soft feed to the animal.",
    ["cow", "buffalo", "goat", "sheep"], ["foot_and_mouth"]
)

print("--- Seeding Complete ---")
print(f"Total diseases: {disease_col.count()}")
print(f"Total knowledge chunks: {knowledge_col.count()}")
