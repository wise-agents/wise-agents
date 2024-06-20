#!/bin/bash
# This script is used to run the model inference server

# it reads the model path and model name from the environment variables
# define these variables before running the script
#export MODEL_PATH=/absolute_path/to/your/model 
#export POD_CONTAINER = podman | docker
#export MODEL_NAME = model_name.gguf

# If a .env file is present, it will read the environment variables from there
# The .env file should be in the same directory as the script
# Rename the .env.example file to .env and set the environment variables
if [ -f ./.env ]; then
	. ./.env
fi

echo "Model path: $MODEL_PATH"
echo "Model name: $MODEL_NAME"
echo "Pod container: $POD_CONTAINER"

$POD_CONTAINER run --rm -it -p 8001:8001 -v $MODEL_PATH:/locallm/models:ro -e MODEL_PATH=models/$MODEL_NAME -e HOST=0.0.0.0 -e PORT=8001 -e MODEL_CHAT_FORMAT=openchat ghcr.io/abetlen/llama-cpp-python:latest 
