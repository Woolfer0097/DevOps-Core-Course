# Use specific version for reproducibility
FROM python:3.13-slim

# Create non-root user (security: don't run as root)
RUN groupadd --gid 1000 appgroup \
    && useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

# Dependencies first (better layer caching: code changes don't invalidate this)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY app.py .

# Own files so non-root user can read
RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 5000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"]
