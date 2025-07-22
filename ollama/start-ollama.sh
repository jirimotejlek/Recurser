#!/bin/bash
set -e

echo "Starting Ollama server..."
# Start Ollama in the background
ollama serve &
OLLAMA_PID=$!

# Function to check if Ollama is ready
check_ollama() {
    curl -s http://localhost:11434/api/tags > /dev/null 2>&1
}

# Wait for Ollama to be ready
echo "Waiting for Ollama to be ready..."
RETRY_COUNT=0
MAX_RETRIES=30
until check_ollama; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "ERROR: Ollama failed to start after $MAX_RETRIES attempts"
        exit 1
    fi
    echo "Waiting for Ollama API... (attempt $RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

echo "Ollama is ready. Pulling model: ${OLLAMA_MODEL:-gemma3n:e2b}"
# Pull the model (default to gemma3n:e2b if not specified)
if ! ollama pull ${OLLAMA_MODEL:-gemma3n:e2b}; then
    echo "ERROR: Failed to pull model ${OLLAMA_MODEL:-gemma3n:e2b}"
    exit 1
fi

echo "Model pulled successfully. Testing model..."
# Test the model with a simple prompt
if ollama run ${OLLAMA_MODEL:-gemma3n:e2b} "Hello, respond with OK if you're working" --verbose; then
    echo "Model test successful!"
else
    echo "WARNING: Model test failed, but continuing..."
fi

echo "Ollama is ready with model: ${OLLAMA_MODEL:-gemma3n:e2b}"
echo "API available at http://localhost:11434"

# Keep the container running by waiting for the Ollama process
wait $OLLAMA_PID