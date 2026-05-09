import os
import json
import pandas as pd
import yaml
import shutil
import sys
from roboflow import Roboflow

# Ensure UTF-8 output for Windows terminals if supported
if sys.stdout.encoding != 'utf-8':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach(), 'replace')

try:
    from inference_sdk import InferenceHTTPClient
except ImportError:
    InferenceHTTPClient = None

ROBOFLOW_DATASETS = [
    {"model_id": "cattle-disease-pnjdc/3", "alias": "cattle_dis_model"},
    {"model_id": "fmd-detection/fmd-cattle", "alias": "fmd_cattle_roboflow"},
    {"model_id": "lsd-cattle/lumpy-skin-disease-detection", "alias": "lsd_roboflow"},
    {"model_id": "dairy-cattle/mastitis-detection", "alias": "mastitis_roboflow"}
]

API_KEY = "aQwkvF35vnNfvxgUUMqu"
DATA_DIR = "data"
RAW_DIR = os.path.join(DATA_DIR, "raw")
PATHS_FILE = os.path.join(DATA_DIR, "download_paths.json")
FAILED_FILE = os.path.join(DATA_DIR, "failed_downloads.txt")

def get_dir_size(start_path='.'):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    return total_size

def process_yolo_to_csv(dataset_path, alias):
    yaml_path = os.path.join(dataset_path, "data.yaml")
    if not os.path.exists(yaml_path):
        return False, "data.yaml not found"
        
    with open(yaml_path, 'r') as f:
        data_yaml = yaml.safe_load(f)
        class_names = data_yaml.get('names', [])
        
    rows = []
    for split in ['train', 'valid', 'test']:
        split_dir = os.path.join(dataset_path, split)
        images_dir = os.path.join(split_dir, "images")
        labels_dir = os.path.join(split_dir, "labels")
        
        if not os.path.exists(images_dir) or not os.path.exists(labels_dir):
            continue
            
        for img_file in os.listdir(images_dir):
            if not img_file.lower().endswith(('.jpg', '.jpeg', '.png')):
                continue
                
            label_file = os.path.splitext(img_file)[0] + ".txt"
            label_path = os.path.join(labels_dir, label_file)
            
            if os.path.exists(label_path):
                with open(label_path, 'r') as lf:
                    lines = lf.readlines()
                    if lines:
                        class_idx = int(lines[0].split()[0])
                        class_label = class_names[class_idx] if class_idx < len(class_names) else f"class_{class_idx}"
                        rows.append({
                            "image_path": os.path.join(split, "images", img_file),
                            "class_label": class_label
                        })
    
    if rows:
        df = pd.DataFrame(rows)
        csv_path = os.path.join(dataset_path, "labels.csv")
        df.to_csv(csv_path, index=False)
        return True, csv_path
    return False, "No valid labels found"

def main():
    if not os.path.exists(RAW_DIR):
        os.makedirs(RAW_DIR)
        
    rf = Roboflow(api_key=API_KEY)
    
    download_paths = {}
    if os.path.exists(PATHS_FILE):
        with open(PATHS_FILE, 'r') as f:
            download_paths = json.load(f)
            
    failed = []
    success_count = 0
    
    print(f"Starting download of {len(ROBOFLOW_DATASETS)} Roboflow datasets...")
    
    for entry in ROBOFLOW_DATASETS:
        model_id = entry["model_id"]
        alias = entry["alias"]
        
        try:
            parts = model_id.split('/')
            
            # Case 1: workspace/project
            # Case 2: project/version
            
            project = None
            version_id = 1
            
            if parts[1].isdigit():
                # project/version
                project = rf.project(parts[0])
                version_id = int(parts[1])
            else:
                # workspace/project
                workspace = rf.workspace(parts[0])
                project = workspace.project(parts[1])
                version_id = 1 # Default to version 1 for universe projects
            
            print(f"Downloading {alias} ({model_id}) version {version_id}...")
            location = os.path.join(RAW_DIR, alias)
            dataset = project.version(version_id).download("yolov8", location=location)
            
            success, result = process_yolo_to_csv(dataset.location, alias)
            if success:
                print(f"[OK] Downloaded and processed {alias} -> {dataset.location}")
                download_paths[alias] = dataset.location
                success_count += 1
            else:
                print(f"[WARN] Warning {alias}: Downloaded but processing failed: {result}")
                download_paths[alias] = dataset.location
                success_count += 1
                
        except Exception as e:
            print(f"[ERROR] Failed {alias}: {e}")
            failed.append(f"{alias} ({model_id}): {str(e)}")
            
    with open(PATHS_FILE, "w") as f:
        json.dump(download_paths, f, indent=4)
        
    if failed:
        with open(FAILED_FILE, "a") as f:
            f.write("\n" + "\n".join(failed))
            
    total_size_bytes = 0
    for alias in [e["alias"] for e in ROBOFLOW_DATASETS]:
        path = download_paths.get(alias)
        if path and os.path.exists(path):
            total_size_bytes += get_dir_size(path)
            
    total_size_gb = total_size_bytes / (1024**3)
    
    print("\n" + "="*30)
    print("ROBOFLOW DOWNLOAD SUMMARY")
    print("="*30)
    print(f"Total attempted : {len(ROBOFLOW_DATASETS)}")
    print(f"Successfully downloaded : {success_count}")
    print(f"Failed : {len(failed)}")
    print(f"Total disk usage : {total_size_gb:.2f} GB")
    print("="*30)

if __name__ == "__main__":
    main()
