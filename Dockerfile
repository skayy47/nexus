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

# Install CPU-only torch first — avoids pulling 2.5 GB CUDA wheels
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install the rest of the package
RUN pip install --no-cache-dir -e "."

# Runtime
COPY demo_corpus/ ./demo_corpus/

COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN sed -i 's/\r//' /docker-entrypoint.sh && chmod +x /docker-entrypoint.sh

EXPOSE 8000

CMD ["/docker-entrypoint.sh"]
