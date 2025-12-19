# DGX-Spark-Recipes

This repo is a collection of things I’ve added, changed, or figured out while working with NVIDIA DGX Spark—beyond what’s covered in the official guides. It includes practical recipes, scripts, and notes from real setups, experiments, and troubleshooting, shared in case they’re useful to others in the community.

## What’s inside
- Playbooks for spinning up and tuning Spark on DGX systems.
- Config snippets for RAPIDS Accelerator, UCX/RDMA, GPU scheduling, and I/O tuning.
- Notes from experiments and benchmarks (what worked, what didn’t, and why).
- Troubleshooting guides for common failure modes and performance pitfalls.
- Utility scripts and one-off helpers used in real clusters.

## Quick start
1. Clone the repo: `git clone https://github.com/<your-org>/DGX-Spark-Recipes.git`
2. Explore by topic (config, tuning, troubleshooting, scripts, notebooks).
3. Try a recipe, capture your results, and adapt the settings to your cluster.

## Environment assumptions
- Access to an NVIDIA DGX system with recent NVIDIA drivers.
- Apache Spark with GPU support (e.g., RAPIDS Accelerator) installed on the cluster.
- CUDA toolkit and UCX/RDMA stack configured when using GPU acceleration and high-speed networking.

## Contributing / sharing back
- Open issues for questions or gaps you notice.
- PRs are welcome—especially new recipes, config diffs, and troubleshooting notes with context.
- Include the hardware/driver/Spark/RAPIDS versions you tested with to help others reproduce.

## License
This project is licensed under the terms of the LICENSE file in this repository.
