# SemantOS — eBPF Method A Overlay

This overlay enables full eBPF in `telemetry-agent` with host kernel headers and mounts.

## Files
- `docker-compose.ebpf.yml` — Compose override file to enable:
  - `privileged: true`, `pid: "host"`
  - Mounts: `/lib/modules`, `/usr/src`, `/sys/kernel/debug`, `/sys/fs/bpf`
  - Env: `USE_EBPF=auto`, `SAMPLE_WINDOW=60`
- `telemetry-agent/Dockerfile` — Adds `kmod` to avoid `modprobe` warning.

## Host Prerequisites
```bash
sudo apt-get update
sudo apt-get install -y linux-headers-$(uname -r)
```

## How to apply
From your project root (the one with your `docker-compose.yml`):

1. **Copy the overlay files**
   ```bash
   cp docker-compose.ebpf.yml /path/to/your/project/
   cp -r telemetry-agent /path/to/your/project/telemetry-agent-overlay
   ```

2. **Update Dockerfile (Option 1: Replace)**
   - Replace your `telemetry-agent/Dockerfile` with the one from `telemetry-agent-overlay/Dockerfile`
     (or merge the `kmod` package into your existing `apt-get install` line).

   **OR Option 2: Edit in place**
   - Edit your existing `telemetry-agent/Dockerfile` and append `kmod` to the install list:
     ```dockerfile
     RUN apt-get update && apt-get install -y --no-install-recommends \
         python3 python3-pip ca-certificates curl \
         bpfcc-tools python3-bpfcc linux-tools-common kmod \
         && rm -rf /var/lib/apt/lists/*
     ```

3. **Start with the override compose file**
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.ebpf.yml build --no-cache telemetry-agent
   docker-compose -f docker-compose.yml -f docker-compose.ebpf.yml up -d
   ```

4. **Verify**
   - `GET http://localhost:9101/healthz` should report `"mode": "ebpf"`
   - `docker logs <telemetry-agent-container>` no longer shows:
     - `modprobe: not found`
     - `chdir(/lib/modules/$(uname -r)/build): No such file or directory`

If you still see errors, ensure the mounts exist on host and versions match the running kernel.
