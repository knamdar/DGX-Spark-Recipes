# ComfyUI Docker for DGX Spark

I built a Docker image to run ComfyUI on DGX Spark and thought sharing it could be helpful.

## Steps
1) Prepare model checkpoints on the DGX (run on the DGX):
```bash
mkdir -p ~/comfyui_checkpoints
cd ~/comfyui_checkpoints
wget https://huggingface.co/Comfy-Org/stable-diffusion-v1-5-archive/resolve/main/v1-5-pruned-emaonly-fp16.safetensors
```

2) Pull the Docker image:
```bash
docker pull knamdar/spark_comfy_ui:v1
```

3) Run ComfyUI (maps port 8188 and mounts checkpoints):
```bash
docker run --rm -it \
  --gpus all \
  -p 8188:8188 \
  -v ~/comfyui_checkpoints:/workspace/ComfyUI/models/checkpoints \
  --name spark_comfy_ui \
  knamdar/spark_comfy_ui:v1 \
  bash -c "cd /workspace/ComfyUI && python main.py --listen 0.0.0.0 --port 8188"
```

4) Open ComfyUI in a browser at `http://DGX_IP_ADDRESS:8188`.

## NVIDIA Sync entry (optional)
1) Connect to your DGX using NVIDIA Sync.
2) Go to Settings -> Custom tab -> +Add New.
3) Name: `ComfyUI`
4) Port: `8188`
5) Check `launch in terminal`.
6) Launch script:
```bash
#!/usr/bin/env bash
set -euo pipefail

IMAGE="knamdar/spark_comfy_ui:v1"
PORT="8188"
CHECKPOINTS="$HOME/comfyui_checkpoints"

# Ensure Docker is available
if ! docker info >/dev/null 2>&1; then
  echo "Error: Docker daemon not reachable." >&2
  exit 1
fi

echo "Starting ComfyUI (ephemeral container)..."
echo "Press Ctrl+C to stop."

docker run --rm -it \
  --gpus all \
  -p ${PORT}:${PORT} \
  -v "${CHECKPOINTS}:/workspace/ComfyUI/models/checkpoints" \
  "${IMAGE}" \
  bash -c "cd /workspace/ComfyUI && python main.py --listen 0.0.0.0 --port ${PORT}"
```
