FROM python:3.11-slim

# System deps for Unstructured (PDF/DOCX parsing)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    poppler-utils \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Deterministic model-cache location: baked at build, found at runtime
# regardless of $HOME / container user (HF Spaces, Render, Fly, Railway).
ENV HF_HOME=/app/.cache/huggingface \
    SENTENCE_TRANSFORMERS_HOME=/app/.cache/sentence-transformers

# Copy dependency manifest first (layer cache)
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install CPU-only torch first — avoids pulling 2.5 GB CUDA wheels
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install the rest of the package
RUN pip install --no-cache-dir -e "."

# Pre-download the embedding model into the image so cold starts are instant.
# chmod so a non-root runtime user (e.g. HF Spaces uid 1000) can read it.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')" \
    && chmod -R a+rX /app/.cache

# Runtime
COPY demo_corpus/ ./demo_corpus/

# Hosts inject $PORT (Render/Railway/Fly). HF Spaces: set app_port: 7860 in the
# Space README and add a PORT=7860 variable. Default 8000 for local docker run.
ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn nexus.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
