# Use official Ollama image which has Ollama perfectly installed
FROM ollama/ollama

# Install python and pip
RUN apt-get update && apt-get install -y python3 python3-pip curl && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy your entire existing project folder into the Hugging Face container
COPY . /app

# Install your Python packages (including the new ollama package from requirements)
RUN pip3 install --no-cache-dir -r requirements.txt --break-system-packages

# Create a startup script that runs Python and Ollama at the same time!
RUN echo '#!/bin/bash\n\
    # Start the Ollama server in the background\n\
    ollama serve &\n\
    sleep 5\n\
    # Pull the specific Llama model down\n\
    ollama pull llama3.2:1b\n\
    # Boot your Flask API!\n\
    gunicorn -b 0.0.0.0:7860 api:app\n\
    ' > /app/start.sh

RUN chmod +x /app/start.sh

EXPOSE 7860
# Execute
CMD ["/app/start.sh"]
