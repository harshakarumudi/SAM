FROM python:3.12-slim

# Install system dependencies for healthcheck and curl
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for principle of least privilege
RUN groupadd -r agriapp && useradd -r -g agriapp agriapp

WORKDIR /workspace

# Install python dependencies
COPY backend/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY backend/ backend/

# Set file permissions and switch to unprivileged user
RUN chown -R agriapp:agriapp /workspace
USER agriapp

EXPOSE 8000

ENV PYTHONUNBUFFERED=1

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
