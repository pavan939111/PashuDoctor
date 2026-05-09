import os
import httpx
import pdfplumber
from bs4 import BeautifulSoup
import json
from tqdm import tqdm
from datetime import datetime

# Define Knowledge Sources
KNOWLEDGE_SOURCES = [
    {
        "url": "https://en.wikipedia.org/wiki/Lumpy_skin_disease",
        "alias": "lumpy_skin_wiki",
        "type": "url"
    },
    {
        "url": "https://www.woah.org/en/disease/lumpy-skin-disease/",
        "alias": "woah_lumpy_skin",
        "type": "url"
    },
    {
        "url": "https://www.fao.org/3/i7330en/I7330EN.pdf",
        "alias": "fao_lumpy_manual",
        "type": "pdf"
    },
    {
        "url": "https://www.aphis.usda.gov/animal_health/downloads/animal_diseases/fmd_factsheet.pdf",
        "alias": "usda_fmd_fact",
        "type": "pdf"
    }
]

# Base directories - relative to project root (pashudoctor/)
BASE_DIR = os.path.join("data", "knowledge_base")
PDF_DIR = os.path.join(BASE_DIR, "pdfs")
TEXT_DIR = os.path.join(BASE_DIR, "texts")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
}

def setup_dirs():
    os.makedirs(PDF_DIR, exist_ok=True)
    os.makedirs(TEXT_DIR, exist_ok=True)

def download_pdf(url, alias):
    path = os.path.join(PDF_DIR, f"{alias}.pdf")
    try:
        with httpx.stream("GET", url, follow_redirects=True, headers=HEADERS, timeout=60.0) as response:
            if response.status_code == 403:
                # Try one more time with simpler headers
                response = httpx.get(url, follow_redirects=True, timeout=30.0)
            
            response.raise_for_status()
            with open(path, "wb") as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)
        return path
    except Exception as e:
        print(f"FAILED {alias}: {e}")
        return None

def extract_pdf_text(pdf_path, alias):
    text_path = os.path.join(TEXT_DIR, f"{alias}.txt")
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(text)
        return text_path, len(text.split())
    except Exception as e:
        print(f"FAILED {alias}: {e}")
        return None, 0

def fetch_url_text(url, alias):
    text_path = os.path.join(TEXT_DIR, f"{alias}.txt")
    try:
        # Use a real browser-like session
        with httpx.Client(headers=HEADERS, follow_redirects=True, timeout=30.0) as client:
            response = client.get(url)
            response.raise_for_status()
            
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Remove junk
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
            
        text = soup.get_text(separator="\n", strip=True)
        
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(text)
        return text_path, len(text.split())
    except Exception as e:
        print(f"FAILED {alias}: {e}")
        return None, 0

def main():
    setup_dirs()
    kb_index = {}
    
    print("Starting Knowledge Base Ingestion...")
    
    for source in KNOWLEDGE_SOURCES:
        url = source["url"]
        alias = source["alias"]
        stype = source["type"]
        
        result = None
        try:
            if stype == "pdf":
                pdf_path = download_pdf(url, alias)
                if pdf_path:
                    txt_path, count = extract_pdf_text(pdf_path, alias)
                    if txt_path:
                        result = {
                            "source_type": "pdf",
                            "original_url": url,
                            "local_text_path": txt_path,
                            "local_pdf_path": pdf_path,
                            "word_count": count,
                            "downloaded_at": datetime.utcnow().isoformat() + "Z"
                        }
            else:
                txt_path, count = fetch_url_text(url, alias)
                if txt_path:
                    result = {
                        "source_type": "url",
                        "original_url": url,
                        "local_text_path": txt_path,
                        "word_count": count,
                        "downloaded_at": datetime.utcnow().isoformat() + "Z"
                    }

            if result:
                kb_index[alias] = result
                # Safely print for Windows console
                print(f"DONE: {alias} -> {result['word_count']} words saved")
        except Exception as e:
            print(f"CRITICAL ERROR {alias}: {e}")

    # Save index
    index_path = os.path.join(BASE_DIR, "kb_index.json")
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(kb_index, f, indent=4)
    
    print(f"\nKnowledge Base indexed: {len(kb_index)} sources processed.")
    print(f"Index saved to: {index_path}")

if __name__ == "__main__":
    main()
