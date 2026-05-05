# PashuDoctor: AI Livestock Health Assistant

PashuDoctor is a production-ready AI-powered platform designed to assist in monitoring and diagnosing livestock health issues. It leverages Multi-Modal RAG (Retrieval-Augmented Generation) to provide accurate insights from images and text.

## Project Structure

```text
pashudoctor/
├── backend/                # FastAPI Application
│   ├── app/                # Core logic, models, and routes
│   ├── tests/              # Unit and integration tests
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile          # Backend containerization
├── frontend/               # UI Application (Streamlit/Flask)
├── data/                   # Data storage for RAG and DB
├── scripts/                # Utility scripts for ingestion and embedding
├── .env.example            # Environment variables template
├── docker-compose.yml      # Orchestration
└── README.md               # Project documentation
```

## Setup Instructions

### 1. Clone the repository
```bash
git clone <repository-url>
cd pashudoctor
```

### 2. Configure Environment Variables
Copy the `.env.example` to `.env` and fill in your API keys.
```bash
cp .env.example .env
```

### 3. Local Installation (Virtual Environment)
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Running with Docker
```bash
docker-compose up --build
```

## Features
- **Image Analysis**: Upload livestock images for health assessment.
- **AI Chat**: Interact with an AI specialist grounded in veterinary knowledge.
- **History Tracking**: Keep track of health cases and diagnosis history.

## Technologies Used
- **Backend**: FastAPI, Pydantic, SQLAlchemy.
- **AI/ML**: Google Gemini Pro Vision, ChromaDB (Vector Search), Ollama.
- **Frontend**: Streamlit / HTML/JS.
- **Containerization**: Docker, Docker Compose.
