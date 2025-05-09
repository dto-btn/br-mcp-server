FROM python:3.12-slim

WORKDIR /app

# Install FreeTDS and build dependencies
RUN apt-get update && apt-get install -y \
    freetds-bin \
    freetds-dev \
    tdsodbc \
    unixodbc-dev \
    gcc \
    g++ \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir uv && \
    uv pip install -e .

# Copy application code
COPY . .

# Expose the port used by MCP server
EXPOSE 8080

# Run the server
CMD ["python", "server.py"]