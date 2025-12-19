# DGX Spark Bundle QSFP Connection

Notes from bringing up a direct QSFP link between two DGX Spark nodes. The official docs cover the wiring, but not enabling both nodes to talk or run multi-node jobs.

## Quick setup (point-to-point)
1) Cable: use the first QSFP port (closest to the power button) on each DGX and ensure both nodes share the same username (replace `USERNAME` below if different).

2) Assign IPs:
```bash
# on DGX1
sudo ip addr add 192.168.100.11/24 dev enp1s0f0np0
sudo ip link set enp1s0f0np0 up

# on DGX2
sudo ip addr add 192.168.100.12/24 dev enp1s0f0np0
sudo ip link set enp1s0f0np0 up

# optional: verify
ip addr show enp1s0f0np0
```

3) Exchange SSH keys on each DGX:
```bash
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa

ssh-copy-id -i ~/.ssh/id_rsa.pub USERNAME@192.168.100.11
ssh-copy-id -i ~/.ssh/id_rsa.pub USERNAME@192.168.100.12
```

4) Verify passwordless SSH from each node:
```bash
ssh 192.168.100.11 hostname
ssh 192.168.100.12 hostname
```

## Notes
- The IPs 192.168.100.11/12 are arbitrary; any small /24 will work if it does not overlap your existing networks. If your Wi-Fi or other LAN already uses 192.168.100.x, pick a different subnet (for example, 192.168.200.11/24 and 192.168.200.12/24).
- Keep this QSFP link on its own network to avoid routing surprises.
- Once SSH is set up, configure your Spark cluster (or other frameworks) to use this interface for inter-node traffic.
