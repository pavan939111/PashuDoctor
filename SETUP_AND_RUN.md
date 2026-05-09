# PashuDoctor — Setup & Run Guide

## Prerequisites
List exact software requirements with versions:
- **Python version required**: 3.9+
- **pip version**: 23.0+
- **OS compatibility**: 
  - **Windows**: Fully supported (tested on Windows 11). Requires Microsoft C++ Build Tools for some ML libraries.
  - **Linux/Mac**: Fully supported. Linux recommended for production deployment.
- **Minimum RAM required**: 8GB (16GB recommended for running Whisper and CLIP simultaneously)
- **Minimum disk space required**: 10GB (includes datasets, ChromaDB, and model weights)
- **Internet required for first setup**: YES (to download models and libraries)
- **Internet required to run**: PARTIAL (offline mode available for STT and translation; RAG works offline; Gemini requires cloud)

## Step 1 — Clone & Navigate
```bash
git clone https://github.com/pavan939111/pashudoctor
cd pashudoctor
```

## Step 2 — Environment Setup

### Creating virtual environment
```bash
python -m venv venv
```

### Activating on Windows
```bash
.\venv\Scripts\activate
```

### Activating on Linux/Mac
```bash
source venv/bin/activate
```

### Installing backend dependencies
```bash
pip install -r backend/requirements.txt
```

### Installing frontend dependencies
```bash
pip install -r frontend/requirements.txt
```

### OS-Specific Notes
- **PyAudio**: 
  - **Windows**: Installs via pip. If it fails, download the pre-compiled wheel from [Unofficial Windows Binaries](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio).
  - **Linux**: Requires `sudo apt-get install python3-pyaudio portaudio19-dev`.
- **Whisper**: Requires `ffmpeg` to be installed on your system PATH.

## Step 3 — Environment Variables
Create a `.env` file in the root directory:

```env
# App Settings
APP_NAME=PashuDoctor
DEBUG=False

# Storage Settings
CHROMA_PATH=./data/chroma_db
CHROMA_COLLECTION=livestock
SQLITE_DB_PATH=./data/pashudoctor.db

# AI/Model Settings
GEMINI_API_KEY=your_primary_key
# Optional: Add multiple keys for rotation (up to 10)
GEMINI_API_KEY_1=your_second_key
GEMINI_API_KEY_2=...

CLIP_MODEL=ViT-B/32
OLLAMA_BASE_URL=http://localhost:11434 (Optional)

# Thresholds
CONFIDENCE_THRESHOLD_LOW=0.50
CONFIDENCE_THRESHOLD_MID=0.75
CONFIDENCE_THRESHOLD_HIGH=0.90

# RAG Weights
DENSE_WEIGHT=0.3
BM25_WEIGHT=0.7
TOP_K_RETRIEVE=20
TOP_K_RERANK=3
```

### How to get a Gemini API key
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey).
2. Create a new API Key (Free tier).
3. Paste it in the `GEMINI_API_KEY` field in `.env`.

### Key Rotation
PashuDoctor automatically rotates through `GEMINI_API_KEY` and `GEMINI_API_KEY_1-10` to manage API rate limits.

## Step 4 — Download Offline Models
```bash
# Whisper small model (244MB, downloads automatically on first run or via this command)
python -c "import whisper; whisper.load_model('small')"

# ArgosTranslate language packages
python scripts/setup_argos.py
```

### scripts/setup_argos.py
This script downloads the required language pairs for offline translation:
```python
import argostranslate.package
argostranslate.package.update_package_index()
available = argostranslate.package.get_available_packages()
langs = ['hi', 'ta', 'te', 'kn', 'ml', 'mr', 'bn', 'pa', 'gu']
for lang in langs:
    # From English to Local
    pkg = next(filter(lambda x: x.from_code == 'en' and x.to_code == lang, available))
    argostranslate.package.install_from_path(pkg.download())
    # From Local to English
    pkg = next(filter(lambda x: x.from_code == lang and x.to_code == 'en', available))
    argostranslate.package.install_from_path(pkg.download())
```

## Step 5 — Data Pipeline
Run these commands in order to build the knowledge base:

```bash
# 1. Download all datasets (Takes ~10 min)
python scripts/download_kaggle.py

# 2. Download Roboflow datasets
python scripts/download_roboflow.py

# 3. Download knowledge base PDFs (Vet manuals)
python scripts/download_knowledge.py

# 4. Build master manifest (Links images to labels)
python scripts/build_manifest.py

# 5. Clean and split dataset
python scripts/clean_and_split.py

# 6. Build BM25 knowledge base (Indexes text chunks)
python scripts/build_kb.py
```

### Estimated Timings:
- **Downloads**: 15-20 minutes depending on internet speed.
- **Manifest/Cleaning**: 2-3 minutes.
- **KB Building**: 1 minute.

## Step 6 — Embed & Index
```bash
# Generate embeddings and populate ChromaDB (Takes 5-15 min on CPU)
python scripts/embed.py

# Verify embeddings are correct
python scripts/verify_embeddings.py
```

**Expected Counts**:
- Disease images: ~5,000+
- Knowledge chunks: ~1,200+

## Step 7 — Run the Application

### Option A — Run Locally (Recommended)
```bash
# Terminal 1: Start Backend API
make run
# OR
uvicorn app.main:app --reload --port 8000 --app-dir backend

# Terminal 2: Start Frontend
make frontend
# OR
streamlit run frontend/app.py --server.port 8501
```

### Option B — Run with Docker
```bash
docker-compose up --build
```

### Option C — Makefile Shortcuts
- `make install`: Install backend dependencies.
- `make run`: Start backend server.
- `make frontend`: Start Streamlit UI.
- `make test`: Run backend unit tests.
- `make docker`: Build and run with Docker.

## Step 8 — Verify Everything is Running
- **API health**: [http://localhost:8000/health](http://localhost:8000/health)
- **API docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Frontend**: [http://localhost:8501](http://localhost:8501)

### Healthy /health Response:
```json
{
  "status": "healthy",
  "services": {
    "api": "online",
    "db": "connected",
    "chromadb": "online"
  }
}
```

## Step 9 — Run Tests
```bash
# Unit tests
pytest backend/tests/ -v

# Integration tests (API must be running)
python scripts/test_api.py

# Evaluation (Performance metrics - takes 20-40 min)
python scripts/evaluate.py
```

## Troubleshooting

### Error: Cannot connect to API
- Check if Terminal 1 (Backend) is still running.
- Ensure no other process is using port 8000.

### Error: ChromaDB collection not found
- Run `python scripts/embed.py` to initialize the database.

### Error: No Gemini API key configured
- Add `GEMINI_API_KEY` to your `.env` file.

### Error: PyAudio not found
- On Windows, use the `.whl` installer. On Linux, install `portaudio19-dev`.

### Error: Whisper model not found
- Run `python -c "import whisper; whisper.load_model('small')"` while connected to the internet.

### Error: ArgosTranslate package missing
- Run `python scripts/setup_argos.py`.

### Error: CUDA out of memory
- The system defaults to CPU. If using GPU, try reducing `batch_size` in `scripts/embed.py`.

### Error: Port 8000 already in use
- Kill the process: `fuser -k 8000/tcp` (Linux) or `stop-process -id (get-nettcpconnection -localport 8000).owningprocess` (PowerShell).

### Error: UnicodeEncodeError (Windows)
- Set environment variable: `set PYTHONUTF8=1`.

## Quick Start (Minimal Setup)
For a 10-minute demo without the full data pipeline:

1. Install dependencies (`pip install -r ...`).
2. Run the demo setup script:
```bash
python scripts/demo_setup.py
```
This script:
- Creates a minimal ChromaDB with 50 sample records.
- Creates a minimal BM25 index.
- Skips the large dataset downloads.
- Prepares the app for immediate launch.
