import kagglehub
import json
import os
import shutil
import sys

# Ensure UTF-8 output for Windows terminals if supported
if sys.stdout.encoding != 'utf-8':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())

KAGGLE_DATASETS = [
    {"slug": "devang03mgr/cattle-diseases-datasets", "alias": "cattle_dis_base"},
    {"slug": "kartikeybartwal/dataset", "alias": "goat_images"},
    {"slug": "gracehephzibahm/animal-disease", "alias": "animal_cond_class"},
    {"slug": "smadive/pet-disease-images", "alias": "pet_disease_imgs"},
    {"slug": "saurabhshahane/lumpy-skin-disease-dataset", "alias": "lumpy_skin_ds"},
    {"slug": "subhashishray/foot-and-mouth-disease-fmd-dataset", "alias": "fmd_ds"},
    {"slug": "mdwaquarazam/cattle-disease-classification", "alias": "cattle_multi_class"},
    {"slug": "anshtanwar/mastitis-cow-detection", "alias": "mastitis_cow_det"},
    {"slug": "rahulbordoloi/buffalo-disease-dataset", "alias": "buffalo_disease"},
    {"slug": "sivaprathishsiva/mastitis-disease-detection", "alias": "mastitis_disease_det"},
    {"slug": "warcoder/lumpy-skin-images-dataset", "alias": "lumpy_skin_imgs"},
    {"slug": "kaushalrimal619/lumpy-skin-disease-cow-images", "alias": "lumpy_skin_cow_imgs"},
    {"slug": "devang03mgr/mastitis-in-cows", "alias": "mastitis_in_cows"}
]

DATA_DIR = "data"
PATHS_FILE = os.path.join(DATA_DIR, "download_paths.json")
FAILED_FILE = os.path.join(DATA_DIR, "failed_downloads.txt")

def get_dir_size(start_path='.'):
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(start_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)
    except Exception:
        pass
    return total_size

def main():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    download_paths = {}
    failed = []
    
    print(f"Starting download of {len(KAGGLE_DATASETS)} datasets...")
    
    for entry in KAGGLE_DATASETS:
        slug = entry["slug"]
        alias = entry["alias"]
        
        try:
            print(f"Downloading {alias} ({slug})...")
            path = kagglehub.dataset_download(slug)
            # Use ASCII-safe symbols for Windows
            print(f"[OK] Downloaded {alias} -> {path}")
            download_paths[alias] = path
        except Exception as e:
            print(f"[ERROR] Failed {alias}: {e}")
            failed.append(f"{alias} ({slug}): {str(e)}")
            
    # Save paths
    with open(PATHS_FILE, "w") as f:
        json.dump(download_paths, f, indent=4)
        
    # Save failures
    if failed:
        with open(FAILED_FILE, "w") as f:
            f.write("\n".join(failed))
            
    # Summary
    success_count = len(download_paths)
    failed_count = len(failed)
    total_size_bytes = 0
    for p in download_paths.values():
        total_size_bytes += get_dir_size(p)
        
    total_size_gb = total_size_bytes / (1024**3)
    
    print("\n" + "="*30)
    print("DOWNLOAD SUMMARY")
    print("="*30)
    print(f"Total attempted : {len(KAGGLE_DATASETS)}")
    print(f"Successfully downloaded : {success_count}")
    print(f"Failed : {failed_count}")
    print(f"Total disk usage : {total_size_gb:.2f} GB")
    print("="*30)

if __name__ == "__main__":
    main()
