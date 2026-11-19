FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UPLOAD_DIR=/app/uploads

WORKDIR /app

# Install system dependencies needed for compiling packages and PostgreSQL drivers
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq-dev \
    gcc \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-hin \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Create upload directory inside container
RUN mkdir -p ${UPLOAD_DIR}

# Copy the rest of the application code
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Start FastAPI application with live reload
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
