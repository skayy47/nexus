FROM python:3.11-slim

# System deps for Unstructured (PDF/DOCX parsing)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    poppler-utils \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency manifest first (layer cache)
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install package with all deps
RUN pip install --no-cache-dir -e "."

# Runtime
COPY demo_corpus/ ./demo_corpus/

EXPOSE 8000

CMD ["uvicorn", "nexus.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
