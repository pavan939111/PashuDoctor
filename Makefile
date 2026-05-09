.PHONY: install run frontend test docker

install:
	pip install -r backend/requirements.txt

run:
	uvicorn backend.app.main:app --reload --port 8000

frontend:
	streamlit run frontend/app.py --server.port 8501

test:
	pytest backend/tests/ -v

docker:
	docker-compose up --build
