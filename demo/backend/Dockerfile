FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
RUN pip install --no-cache-dir uv

# Copy the main package (langgraph-checkpoint-neo4j)
COPY pyproject.toml /app/pyproject.toml
COPY README.md /app/README.md
COPY langgraph/ /app/langgraph/

# Install the main checkpointer package
RUN uv pip install --system -e /app

# Copy backend application
COPY demo/backend/app/ /app/app/

# Install backend dependencies
RUN uv pip install --system \
    fastapi \
    "uvicorn[standard]" \
    pydantic \
    pydantic-settings \
    langgraph \
    langchain-openai \
    neo4j

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
