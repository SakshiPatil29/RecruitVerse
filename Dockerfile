FROM python:3.11-slim

WORKDIR /app

# System deps for pymupdf / sentence-transformers wheels.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501 8000

# Default: run the Streamlit ATS UI. Override the command to run the API instead:
#   uvicorn src.api.main:app --host 0.0.0.0 --port 8000
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]
