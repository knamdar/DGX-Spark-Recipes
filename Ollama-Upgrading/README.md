# Upgrading Ollama

## Problem

When pulling the Open WebUI image with Ollama, the Ollama version is not necessarily the latest:

```bash
docker pull ghcr.io/open-webui/open-webui:ollama
```
## Reference

For more information, see: [NVIDIA Spark + Open WebUI](https://build.nvidia.com/spark/open-webui)

## Solution

To upgrade Ollama to the latest version, run the following command inside the container:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

## Committing the Changes

After upgrading Ollama, commit the container to save the changes:

```bash
docker commit CONTAINER_ID open-webui-ollama:updated
```