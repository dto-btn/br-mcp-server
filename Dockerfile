FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    gnupg2 \
    ca-certificates \
    build-essential \
    unixodbc-dev \
    libssl-dev \
    libkrb5-dev && \
    # Install Microsoft ODBC Driver 18 for SQL Server
    curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > /usr/share/keyrings/microsoft-prod.gpg && \
    curl https://packages.microsoft.com/config/debian/12/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql18 && \
    rm -rf /var/lib/apt/lists/*

# Copy pyproject.toml and install dependencies with UV
COPY pyproject.toml ./

# Create virtual environment
RUN uv venv .venv
ENV PATH="/app/.venv/bin:$PATH"

# Install project dependencies (including pyodbc)
RUN uv pip install -e .

# Copy your server script, business_request module, and environment files
COPY server.py ./
COPY business_request/ ./business_request/

EXPOSE 8000

CMD ["python", "server.py"]