# RustDesk

With a combination of TailScale and RustDesk, access your computers limitlessly. Say bye to all the remote desktop apps you are using.

## Installation guide

On your DGX Spark:

### 1️⃣ Pull once
```bash
docker pull rustdesk/rustdesk-server:latest
```

### 2️⃣ Create a persistent data directory
```bash
mkdir -p /opt/rustdesk
sudo chown -R $USER:$USER /opt/rustdesk
```

### 3️⃣ Run hbbs (ID server)
```bash
docker run -d \
  --name rustdesk-hbbs \
  --restart unless-stopped \
  -v /opt/rustdesk:/root \
  -p 21115:21115/tcp \
  -p 21116:21116/tcp \
  -p 21116:21116/udp \
  -p 21118:21118/tcp \
  rustdesk/rustdesk-server:latest hbbs
```

### 4️⃣ Run hbbr (relay server)
```bash
docker run -d \
  --name rustdesk-hbbr \
  --restart unless-stopped \
  -v /opt/rustdesk:/root \
  -p 21117:21117/tcp \
  -p 21119:21119/tcp \
  rustdesk/rustdesk-server:latest hbbr
```

**(Optional) Add web-client support later**

Only if you need browser-based access:

- `hbbs` already includes: `-p 21118:21118/tcp`
- `hbbr` already includes: `-p 21119:21119/tcp`

You can add these later by recreating containers — not required initially.

That's it.
No compose.
No YAML.
No abstraction.

## Verify
```bash
docker ps
```
You should see:
- `rustdesk-hbbs`
- `rustdesk-hbbr`

## Get the server public key (clients need this)
```bash
docker logs rustdesk-hbbs | grep "key"
```

## Configure RustDesk client
In RustDesk client:
1. Click ☰ Menu → Settings
2. Go to Network
3. Fill in:

| Field | Value |
|-------|-------|
| ID Server | DGX_IP_OR_HOSTNAME |
| Relay Server | DGX_IP_OR_HOSTNAME |
| API Server | (leave empty) |
| Key | (paste server key) |

> **Note:** you do not need to have a DGX to be able to implement RustDesk server.
