# Backend API + scheduler. Build from the repository root:
#   docker build -t engineerd-api .
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app/Backend

# Dependencies first, so code changes don't reinstall everything.
COPY Backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt \
    && playwright install --with-deps chromium

COPY Backend/ ./
# Migrations live beside the backend, one level up.
COPY database/ /app/database/

# One worker only: the scheduler runs inside each process.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
