import os
import json
import uuid
import pandas as pd
from tqdm import tqdm

# Configuration
PATHS_FILE = os.path.join("data", "download_paths.json")
OUTPUT_FILE = os.path.join("data", "processed", "master_manifest.csv")

LABEL_MAP = {
    "foot-and-mouth": "foot_and_mouth",
    "foot_and_mouth": "foot_and_mouth",
    "foot and mouth": "foot_and_mouth",
    "FMD": "foot_and_mouth",
    "mastitis": "mastitis",
    "Mastitis": "mastitis",
    "mastitis_infection": "mastitis",
    "lumpy": "lumpy_skin_disease",
    "LSD": "lumpy_skin_disease",
    "lumpy skin": "lumpy_skin_disease",
    "lumpy_skin": "lumpy_skin_disease",
    "lumpyskin": "lumpy_skin_disease",
    "BQ": "blackquarter",
    "black-quarter": "blackquarter",
    "black_quarter": "blackquarter",
    "black quarter": "blackquarter",
    "HS": "hemorrhagic_septicemia",
    "hemorrhagic": "hemorrhagic_septicemia",
    "haemorrhagic": "hemorrhagic_septicemia",
    "hemorrhagic_septicemia": "hemorrhagic_septicemia",
    "PPR": "ppr",
    "peste des petits": "ppr",
    "healthy": "healthy",
    "normal": "healthy",
    "Healthy": "healthy",
    "infected": "unknown_disease",
    "diseased": "unknown_disease",
    "sick": "unknown_disease"
}

ANIMAL_MAP = {
    "cow": "cow",
    "cattle": "cow",
    "bovine": "cow",
    "buffalo": "buffalo",
    "bubaline": "buffalo",
    "goat": "goat",
    "caprine": "goat",
    "sheep": "sheep",
    "ovine": "sheep"
}

def normalize_label(label):
    if not label:
        return "unknown"
    label_low = label.lower().replace("-", " ").replace("_", " ")
    for key, val in LABEL_MAP.items():
        key_low = key.lower().replace("-", " ").replace("_", " ")
        if key_low in label_low:
            return val
    return "unknown_disease"

def detect_animal(path):
    path_lower = path.lower()
    for key, val in ANIMAL_MAP.items():
        if key in path_lower:
            return val
    return "unknown"

def main():
    if not os.path.exists(PATHS_FILE):
        print(f"FAILED: {PATHS_FILE} not found.")
        return

    with open(PATHS_FILE, "r") as f:
        download_paths = json.load(f)

    manifest_records = []
    valid_extensions = (".jpg", ".jpeg", ".png", ".webp", ".bmp")

    print("Building Master Manifest...")

    for alias, source_path in download_paths.items():
        if not os.path.exists(source_path):
            continue

        print(f" Processing {alias}...")
        
        labels_df = None
        labels_csv = os.path.join(source_path, "labels.csv")
        if os.path.exists(labels_csv):
            try:
                labels_df = pd.read_csv(labels_csv)
            except Exception:
                pass

        for root, dirs, files in os.walk(source_path):
            for file in files:
                if file.lower().endswith(valid_extensions):
                    img_abs_path = os.path.abspath(os.path.join(root, file))
                    
                    original_label = "unknown"
                    if labels_df is not None:
                        match = labels_df[labels_df['image_path'].str.contains(file, na=False)]
                        if not match.empty:
                            original_label = match.iloc[0]['class_label']
                    
                    if original_label == "unknown" or pd.isna(original_label):
                        original_label = os.path.basename(root)

                    disease = normalize_label(original_label)
                    animal = detect_animal(img_abs_path)
                    
                    if alias in ANIMAL_MAP:
                        animal = ANIMAL_MAP[alias]

                    manifest_records.append({
                        "image_id": str(uuid.uuid4()),
                        "image_path": img_abs_path,
                        "dataset_source": alias,
                        "original_label": original_label,
                        "animal_type": animal,
                        "disease_label": disease,
                        "split": "unassigned"
                    })

    df = pd.DataFrame(manifest_records)
    df.to_csv(OUTPUT_FILE, index=False)

    # Print Summary
    total = len(df)
    animals = df['animal_type'].value_counts()
    diseases = df['disease_label'].value_counts()

    print("\n")
    print("       Master Manifest Summary           ")
    print("")
    print(f" Total images found   {total:<17} ")
    print(f" Cattle / Cow         {animals.get('cow', 0):<17} ")
    print(f" Buffalo              {animals.get('buffalo', 0):<17} ")
    print(f" Goat                 {animals.get('goat', 0):<17} ")
    print(f" Sheep                {animals.get('sheep', 0):<17} ")
    print(f" Unknown animal       {animals.get('unknown', 0):<17} ")
    print("")
    print(f" foot_and_mouth       {diseases.get('foot_and_mouth', 0):<17} ")
    print(f" mastitis             {diseases.get('mastitis', 0):<17} ")
    print(f" lumpy_skin_disease   {diseases.get('lumpy_skin_disease', 0):<17} ")
    print(f" blackquarter         {diseases.get('blackquarter', 0):<17} ")
    print(f" hemorrhagic_sep      {diseases.get('hemorrhagic_septicemia', 0):<17} ")
    print(f" ppr                  {diseases.get('ppr', 0):<17} ")
    print(f" healthy              {diseases.get('healthy', 0):<17} ")
    print(f" unknown_disease      {diseases.get('unknown_disease', 0):<17} ")
    print("")

if __name__ == "__main__":
    main()
