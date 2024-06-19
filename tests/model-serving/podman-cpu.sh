podman pull quay.io/ai-lab/llamacpp_python
podman run --rm -it -p 8001:8001 -v ../../models:/locallm/models:ro -e MODEL_PATH=models/granite-7b-lab-Q4_K_M.gguf -e HOST=0.0.0.0 -e PORT=8001 -e MODEL_CHAT_FORMAT=openchat llamacpp_python 
