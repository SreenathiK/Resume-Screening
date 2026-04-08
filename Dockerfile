FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    openenv-core[core] \
    fastapi \
    uvicorn \
    pydantic \
    groq \
    openai \
    requests

# Copy application code
COPY . .

# Create server directory if it doesn't exist and add __init__.py files
RUN mkdir -p /app/server && \
    touch /app/__init__.py && \
    touch /app/server/__init__.py

# Set environment variables
ENV PYTHONPATH="/app:$PYTHONPATH"
ENV RESUME_DIFFICULTY="easy"

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the server
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]