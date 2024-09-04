#!/bin/bash
# This script is used to run the model inference server

# it reads the model path and model name from the environment variables
# define these variables before running the script
#export MODEL_PATH=/absolute_path/to/your/model 
export POD_CONTAINER="${POD_CONTAINER:-docker}"
export MODEL_VOLUME="${MODEL_VOLUME:-model_path}"
export MODEL_NAME="${MODEL_NAME:-granite-7b-lab-Q4_K_M.gguf}"
export MODEL_PATH="${MODEL_PATH:-./granite-7b-lab-GGUF}"

# If a .env file is present, it will read the environment variables from there
# The .env file should be in the same directory as the script
# Rename the .env.example file to .env and set the environment variables
WORKING_DIR="$(dirname "${BASH_SOURCE[0]}")"
if [ -f $WORKING_DIR/.env ]; then
       . $WORKING_DIR/.env
fi

$POD_CONTAINER volume ls | grep $MODEL_VOLUME
if [ $? -ne 0 ]; then
    echo "Creating volume " $MODEL_VOLUME
    $POD_CONTAINER volume create $MODEL_VOLUME
else
     echo "Volume " $MODEL_VOLUME " already exists"
fi

export VOLUME_PATH="$($POD_CONTAINER volume inspect --format '{{ .Mountpoint }}' $MODEL_VOLUME)"

echo "Volume path: $VOLUME_PATH"
echo "Model path: $MODEL_PATH"
echo "Model name: $MODEL_NAME"
echo "Pod container: $POD_CONTAINER"
echo "Copying GGUF file: cp -f $MODEL_PATH/$MODEL_NAME $VOLUME_PATH/$MODEL_NAME"

$POD_CONTAINER container create --name dummy -v $VOLUME_PATH:/root hello-world
$POD_CONTAINER cp  $MODEL_PATH/$MODEL_NAME dummy:/root/$MODEL_NAME
$POD_CONTAINER rm dummy

$POD_CONTAINER run --rm -it -p 8001:8001 -v $MODEL_VOLUME:/locallm/models:ro -e MODEL=/locallm/models/$MODEL_NAME -e HOST=0.0.0.0 -e PORT=8001 -e MODEL_CHAT_FORMAT=openchat ghcr.io/abetlen/llama-cpp-python:latest
