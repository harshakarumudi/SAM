FROM python:3.12-slim

# Create non-root system user
RUN groupadd -r iotuser && useradd -r -g iotuser iotuser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY simulator.py .

# Switch to non-root user
USER iotuser

ENV PYTHONUNBUFFERED=1

CMD ["python", "simulator.py", "--loop", "--interval", "5"]
