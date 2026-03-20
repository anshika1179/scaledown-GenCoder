# Use a lightweight Python machine
FROM python:3.10-slim

# Install system utilities needed for Ollama
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install Ollama directly from binary to avoid systemd errors in Docker
RUN curl -L https://ollama.com/download/ollama-linux-amd64 -o /usr/bin/ollama \
    && chmod +x /usr/bin/ollama

# Set the working directory
WORKDIR /app

# Copy your entire existing project folder into the Hugging Face container
COPY . /app

# Install your Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Create a startup script that runs Python and Ollama at the same time!
RUN echo '#!/bin/bash\n\
    # Start the Ollama server in the background\n\
    ollama serve &\n\
    # Wait a few seconds for exactly Ollama to start cleanly\n\
    sleep 5\n\
    # Pull the specific Llama model down\n\
    ollama pull llama3.2:1b\n\
    # Boot your Flask API!\n\
    gunicorn -b 0.0.0.0:7860 api:app\n\
    ' > /app/start.sh

RUN chmod +x /app/start.sh

# Hugging Face Spaces strictly requires applications to run on port 7860
EXPOSE 7860

# Execute
CMD ["/app/start.sh"]
