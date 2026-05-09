# PashuDoctor Pre-Demo Checklist ✅

## 1. Environment & Connectivity
- [ ] Internet Connection: High-speed stable connection (for Gemini API).
- [ ] `.env` file: Ensure `GEMINI_API_KEY` is present and valid.
- [ ] Backend Running: `uvicorn app.main:app` should be active on port 8000.

## 2. Data Readiness
- [ ] ChromaDB: Verify `data/chroma_db` is populated.
- [ ] Dataset: Ensure the Kaggle dataset is available at the expected path for local demo images.
- [ ] Logs: Check `logs/pashudoctor.log` is writable.

## 3. Demo Flow
- [ ] Open Browser: Have `http://localhost:8000/docs` ready to show the API.
- [ ] Terminal 1: Backend logs (for rotation visibility).
- [ ] Terminal 2: `demo/run_demo.py` ready to execute.
- [ ] Talking Points: Have `demo/TALKING_POINTS.md` open for reference.

## 4. Troubleshooting
- **429 Quota Exceeded**: The system should rotate keys automatically. If it still fails, wait 60s.
- **Connection Error**: Check if the backend is running and the port isn't blocked.
- **Empty Results**: Ensure the database was correctly ingested using `scripts/ingest_data.py`.
