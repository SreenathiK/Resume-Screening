FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    pydantic \
    httpx

# Copy application
COPY . .

# Set environment variables
ENV PYTHONPATH="/app:$PYTHONPATH"

EXPOSE 7860

CMD uvicorn server.app:app --host 0.0.0.0 --port 7860