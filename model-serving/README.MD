# How to start a local inference for your model

## Download the model

Download a (small) model from https://huggingface.co/models
Good oprtions are:
* granite-7b-lab-Q4_K_M.gguf
* Phi-3-mini-4k-instruct-q4.gguf

The model need to be in gguf format. You have 2 option

1. Filter for GGUF models in hugging face
2. Download in HF format and convert it to gguf https://github.com/ggerganov/llama.cpp/blob/master/convert-hf-to-gguf.py

## running Lllama cpp image

There is a script named model_inference.sh in the same directory of this document. The script run the model inference server

It reads the model path and model name from the environment variables, define these variables before running the script

```   
    export MODEL_PATH=/absolute_path/to/your/model
 
    export POD_CONTAINER=podman | docker

    export MODEL_NAME=model_name.gguf
  ```

If a .env file is present, it will read the environment variables from there
The .env file should be in the same directory as the script

Rename the .env.example file to .env and set the environment variables