import os
import json
from datetime import datetime

# Configuration
KB_INDEX_PATH = os.path.join("data", "knowledge_base", "kb_index.json")
TEXT_DIR = os.path.join("data", "knowledge_base", "texts")
OUTPUT_CHUNKS = os.path.join("data", "knowledge_base", "chunks.jsonl")
OUTPUT_DESCRIPTIONS = os.path.join("data", "knowledge_base", "disease_descriptions.json")

DISEASE_KEYWORDS = {
    "foot_and_mouth": ["foot and mouth", "fmd", "aphthous fever"],
    "mastitis": ["mastitis", "udder infection", "mammary gland"],
    "lumpy_skin": ["lumpy skin", "lsd", "neethling virus"],
    "blackquarter": ["blackquarter", "black quarter", "blackleg", "clostridium chauvoei"],
    "hemorrhagic_septicemia": ["hemorrhagic septicemia", "hs", "pasteurella multocida"],
    "ppr": ["ppr", "peste des petits", "goat plague"],
    "healthy": ["healthy", "normal", "prevention", "vaccination"]
}

ANIMAL_KEYWORDS = {
    "cow": ["cow", "cattle", "bovine", "calf", "ox"],
    "buffalo": ["buffalo", "water buffalo", "bubaline"],
    "goat": ["goat", "caprine", "kid"],
    "sheep": ["sheep", "ovine", "lamb"]
}

def chunk_text(text, chunk_size=300, overlap=50):
    words = text.split()
    chunks = []
    
    if len(words) < 80:
        return []
        
    for i in range(0, len(words), chunk_size - overlap):
        chunk_words = words[i:i + chunk_size]
        if len(chunk_words) < 80:
            continue
        chunks.append(" ".join(chunk_words))
        
    return chunks

def detect_tags(text, keyword_map):
    tags = []
    text_lower = text.lower()
    for tag, keywords in keyword_map.items():
        for kw in keywords:
            if kw in text_lower:
                tags.append(tag)
                break
    return tags

def main():
    if not os.path.exists(KB_INDEX_PATH):
        print(f"FAILED: {KB_INDEX_PATH} not found.")
        return

    with open(KB_INDEX_PATH, "r") as f:
        kb_index = json.load(f)

    all_chunks = []
    source_counts = {}

    print("Building Knowledge Base Chunks...")

    for alias, metadata in kb_index.items():
        text_path = metadata["local_text_path"]
        # Ensure path is relative to where we run the script (pashudoctor/)
        if not os.path.exists(text_path):
            # Try absolute or fixing path
            text_path = os.path.join(TEXT_DIR, os.path.basename(text_path))
            if not os.path.exists(text_path):
                print(f"⚠️  Skipping {alias}: {text_path} not found.")
                continue

        with open(text_path, "r", encoding="utf-8") as f:
            content = f.read()

        chunks = chunk_text(content)
        source_counts[alias] = len(chunks)

        for i, chunk_text_content in enumerate(chunks):
            chunk_record = {
                "chunk_id": f"{alias}_{i}",
                "text": chunk_text_content,
                "source": alias,
                "disease_tags": detect_tags(chunk_text_content, DISEASE_KEYWORDS),
                "animal_tags": detect_tags(chunk_text_content, ANIMAL_KEYWORDS),
                "word_count": len(chunk_text_content.split())
            }
            all_chunks.append(chunk_record)

    # Save chunks.jsonl
    with open(OUTPUT_CHUNKS, "w", encoding="utf-8") as f:
        for chunk in all_chunks:
            f.write(json.dumps(chunk) + "\n")

    # Create and save disease_descriptions.json
    disease_descriptions = {
        "foot_and_mouth": (
            "Foot-and-Mouth Disease (FMD) is a highly contagious viral disease that affects cloven-hoofed animals including cattle, buffalo, sheep, and goats. "
            "It is characterized by high fever, followed by the appearance of blisters (vesicles) inside the mouth and on the feet, which may rupture and cause lameness. "
            "The disease causes significant economic losses due to decreased milk production, weight loss, and trade restrictions. While adult animals usually survive, mortality can be high in young animals due to heart damage."
        ),
        "mastitis": (
            "Mastitis is the inflammation of the mammary gland and udder tissue, usually caused by bacterial infection following trauma or pathogen entry via the teat canal. "
            "Symptoms include swelling, heat, redness, and pain in the udder, alongside visible abnormalities in the milk such as clots, flakes, or a watery appearance. "
            "Subclinical mastitis is particularly dangerous as it lacks visible symptoms but significantly reduces milk quality and yield, requiring diagnostic tests like the California Mastitis Test (CMT) for detection."
        ),
        "lumpy_skin_disease": (
            "Lumpy Skin Disease (LSD) is a viral infection of cattle and buffalo transmitted by blood-feeding insects like flies, mosquitoes, and ticks. "
            "The disease is marked by the eruption of firm, painful nodules (lumps) on the skin, which can cover the entire body, leading to secondary infections and permanent skin damage. "
            "Infected animals often suffer from high fever, reduced milk yield, and enlarged lymph nodes. Vaccination and insect control are the primary methods of prevention in endemic regions."
        ),
        "blackquarter": (
            "Blackquarter (BQ), also known as Blackleg, is an acute, febrile, highly fatal bacterial disease of cattle and sheep caused by Clostridium chauvoei spores. "
            "It typically affects rapidly growing young cattle in good condition, manifesting as crepitant swelling in heavy muscle areas like the rump, chest, or neck. "
            "The disease progresses rapidly, often leading to sudden death within 12 to 48 hours. Carcasses often exhibit a characteristic rancid butter smell in the affected muscle tissue."
        ),
        "hemorrhagic_septicemia": (
            "Hemorrhagic Septicemia (HS) is a severe bacterial disease characterized by rapid onset and high mortality, primarily affecting cattle and water buffalo in tropical climates. "
            "Key symptoms include high fever, loud breathing (stridor), and hot, painful swelling in the throat and brisket area, which can lead to suffocation. "
            "The disease is often triggered by environmental stress such as the onset of the monsoon season. Early antibiotic treatment is critical, though death often occurs before treatment can begin."
        ),
        "ppr": (
            "PPR (Peste des Petits Ruminants), also known as Sheep and Goat Plague, is a devastating viral disease affecting small ruminants. "
            "Infected animals exhibit high fever, erosive sores in the mouth, nasal and ocular discharge, and severe pneumonia or diarrhea. "
            "The disease spreads through direct contact and can wipe out entire herds, with mortality rates reaching up to 90% in naive populations. Global eradication programs are currently active to eliminate this threat."
        ),
        "healthy_cattle": (
            "Healthy cattle exhibit bright eyes, a moist muzzle, and a smooth, shiny coat. They have a consistent appetite, regular rumination (chewing the cud), and maintain steady social interactions with the herd. "
            "Normal rectal temperatures for adult cattle range between 100.4F and 102.8F (38C to 39.3C), with a pulse rate of 40-70 beats per minute and a respiration rate of 10-30 breaths per minute. "
            "Regular preventive care, including timely vaccinations, deworming, and balanced nutrition, is essential to maintaining this healthy state and ensuring peak productivity."
        )
    }

    with open(OUTPUT_DESCRIPTIONS, "w", encoding="utf-8") as f:
        json.dump(disease_descriptions, f, indent=4)

    # Print Summary
    print(f"\nTotal chunks created: {len(all_chunks)}")
    print("\nChunks per source:")
    print("-" * 30)
    for source, count in source_counts.items():
        print(f"{source:<20} | {count}")
    
    covered = set()
    for chunk in all_chunks:
        covered.update(chunk["disease_tags"])
    
    print("\nDiseases covered:")
    print(", ".join(sorted(covered)) if covered else "None")
    print("\nReady for BM25 indexing: YES")

if __name__ == "__main__":
    main()
