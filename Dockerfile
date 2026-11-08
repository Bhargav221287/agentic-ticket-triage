FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install minimal system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency manifest and install packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code, knowledge base, UI, and scripts
COPY app/ app/
COPY kb/ kb/
COPY ui/ ui/
COPY scripts/ scripts/
COPY pyproject.toml .
COPY README.md .

# Expose FastAPI backend (8000) and Streamlit frontend (8501)
EXPOSE 8000 8501

# Default launch command runs the FastAPI backend
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
