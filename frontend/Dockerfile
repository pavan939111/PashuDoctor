FROM python:3.10-slim

WORKDIR /app

# Reusing backend requirements for simplicity or I could create a frontend/requirements.txt
# Since Streamlit is not in backend requirements, I should probably add it.
RUN pip install --no-cache-dir streamlit requests python-dotenv

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
