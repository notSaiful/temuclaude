# Timuclaude Dockerfile
# For deployment to Fly.io, Railway, or any container platform

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY config/ ./config/
COPY benchmarks/ ./benchmarks/
COPY tests/ ./tests/
COPY start.sh ./
COPY README.md ./

# Make start script executable
RUN chmod +x start.sh

# Set environment defaults
ENV TIMUCLAUDE_MASTER_KEY=change-me
ENV OLLAMA_API_BASE=http://localhost:11434
ENV LITELLM_PORT=4000

# Expose LiteLLM proxy port
EXPOSE 4000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:4000/health || exit 1

# Start the LiteLLM proxy
CMD ["python", "-m", "litellm", "--config", "config/litellm.yaml", "--port", "4000", "--host", "0.0.0.0"]