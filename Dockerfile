# Use a lightweight Python image — no Ollama needed
FROM python:3.10-slim

# Install system deps for PyMuPDF and FAISS
RUN apt-get update && apt-get install -y \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 7860 (required by Hugging Face Spaces)
EXPOSE 7860

# Launch the Flask app via gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:7860", "--timeout", "120", "--workers", "1", "--worker-class", "gevent", "api:app"]
