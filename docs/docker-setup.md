# Agent Zero - Local Docker Setup Guide

This guide will help you build and run your own custom Docker container for Agent Zero locally.

## 📋 Prerequisites

- **Docker Desktop** (Windows/Mac) or **docker-ce** (Linux) installed and running
- At least 8GB of RAM available for Docker
- 10GB of free disk space

## 🚀 Quick Start

### Option 1: Using Helper Scripts (Recommended)

**Windows (PowerShell):**
```powershell
# Build the Docker image
.\docker-build.ps1

# Run the container
.\docker-run.ps1 -Detached

# Access at http://localhost:50080
```

**Linux/Mac (Bash):**
```bash
# Make scripts executable (first time only)
chmod +x *.sh

# Build the Docker image
./docker-build.sh

# Run the container
./docker-run.sh --detached

# Access at http://localhost:50080
```

### Option 2: Using Docker Compose

```bash
# Build and run in one command
docker-compose -f docker-compose.local.yml up -d

# Access at http://localhost:50080
```

### Option 3: Manual Docker Commands

```bash
# Build the image
docker build -f DockerfileLocal -t agent-zero-local --build-arg CACHE_DATE=$(date +%Y-%m-%d:%H:%M:%S) .

# Run the container
docker run -d \
  --name agent-zero-local \
  -p 50080:80 \
  -p 55022:22 \
  -v $(pwd)/agent-zero-data/memory:/a0/memory \
  -v $(pwd)/agent-zero-data/knowledge:/a0/knowledge \
  -v $(pwd)/agent-zero-data/logs:/a0/logs \
  agent-zero-local

# Access at http://localhost:50080
```

## 📁 Directory Structure

After setup, you'll have:

```
agent-zero/
├── agent-zero-data/          # Persistent data (created automatically)
│   ├── memory/               # Agent's memory storage
│   ├── knowledge/            # Knowledge base files
│   │   └── custom/           # Your custom knowledge
│   ├── instruments/          # Custom instruments
│   │   └── custom/
│   ├── logs/                 # Agent logs
│   └── tmp/                  # Temporary files
├── docker-compose.local.yml  # Docker Compose configuration
├── docker-build.ps1/.sh      # Build helper scripts
├── docker-run.ps1/.sh        # Run helper scripts
├── docker-stop.ps1/.sh       # Stop helper scripts
├── docker-logs.ps1/.sh       # Logs helper scripts
└── DOCKER-SETUP.md           # This file
```

## 🔧 Configuration

### Port Configuration

Default ports:
- **Web UI**: 50080 → Container port 80
- **SSH**: 55022 → Container port 22

To change ports:

1. **Edit `docker-compose.local.yml`**:
   ```yaml
   ports:
     - "8080:80"    # Change 50080 to 8080
     - "2222:22"    # Change 55022 to 2222
   ```

2. **Or use environment variables**:
   ```bash
   # Windows PowerShell
   $env:WEB_PORT="8080"
   $env:SSH_PORT="2222"
   .\docker-run.ps1 -Detached

   # Linux/Mac
   WEB_PORT=8080 SSH_PORT=2222 ./docker-run.sh --detached
   ```

### Data Persistence

Your data is stored in `agent-zero-data/` directory and automatically mounted to the container.

**⚠️ Important Notes:**
- The backup/restore feature (in Web UI) is the **recommended** way to persist data
- Mapping the entire `/a0` directory can cause issues when upgrading Agent Zero versions
- Current setup maps only specific subdirectories to avoid conflicts

**What's Persisted:**
- ✅ Memory (agent's learned information)
- ✅ Knowledge base
- ✅ Custom instruments
- ✅ Logs
- ❌ Settings (use backup/restore in Web UI)
- ❌ API Keys (configure in Web UI or mount .env file)

### Optional: Persist Settings and API Keys

To persist `.env` file with API keys:

1. Create `.env` file in `agent-zero-data/`
2. Uncomment this line in `docker-compose.local.yml`:
   ```yaml
   # - ./agent-zero-data/.env:/a0/.env
   ```
3. Rebuild and restart the container

## 📚 Helper Scripts Reference

### Build Scripts

**PowerShell:**
```powershell
# Normal build with cache
.\docker-build.ps1

# Clean build without cache
.\docker-build.ps1 -NoCache

# Custom tag
.\docker-build.ps1 -Tag "my-agent-zero"
```

**Bash:**
```bash
# Normal build with cache
./docker-build.sh

# Clean build without cache
./docker-build.sh --no-cache

# Custom tag
./docker-build.sh --tag "my-agent-zero"
```

### Run Scripts

**PowerShell:**
```powershell
# Run in detached mode (background)
.\docker-run.ps1 -Detached

# Build and run
.\docker-run.ps1 -Build -Detached

# Run in foreground (see logs)
.\docker-run.ps1
```

**Bash:**
```bash
# Run in detached mode (background)
./docker-run.sh --detached

# Build and run
./docker-run.sh --build --detached

# Run in foreground (see logs)
./docker-run.sh
```

### Stop Scripts

**PowerShell:**
```powershell
# Stop container (preserves data)
.\docker-stop.ps1

# Stop and remove container
.\docker-stop.ps1 -Remove
```

**Bash:**
```bash
# Stop container (preserves data)
./docker-stop.sh

# Stop and remove container
./docker-stop.sh --remove
```

### Log Scripts

**PowerShell:**
```powershell
# View last 100 lines
.\docker-logs.ps1

# Follow logs in real-time
.\docker-logs.ps1 -Follow

# View last 500 lines
.\docker-logs.ps1 -Lines 500
```

**Bash:**
```bash
# View last 100 lines
./docker-logs.sh

# Follow logs in real-time
./docker-logs.sh --follow

# View last 500 lines
./docker-logs.sh --lines 500
```

## 🔍 Docker Compose Commands

All standard docker-compose commands work:

```bash
# Start container
docker-compose -f docker-compose.local.yml up -d

# Stop container
docker-compose -f docker-compose.local.yml down

# View logs
docker-compose -f docker-compose.local.yml logs -f

# Restart container
docker-compose -f docker-compose.local.yml restart

# Rebuild image
docker-compose -f docker-compose.local.yml build --no-cache

# View status
docker-compose -f docker-compose.local.yml ps
```

## 🐛 Troubleshooting

### Container won't start

**Check logs:**
```bash
docker logs agent-zero-local
```

**Check if ports are available:**
```bash
# Windows
netstat -ano | findstr :50080

# Linux/Mac
lsof -i :50080
```

### Build fails with "base image not found"

**Pull the base image first:**
```bash
docker pull agent0ai/agent-zero-base:latest
```

### Out of disk space

**Clean up Docker:**
```bash
# Remove unused images
docker image prune -a

# Remove all stopped containers
docker container prune

# Full cleanup (WARNING: removes all unused Docker data)
docker system prune -a --volumes
```

### Permission errors on Linux/Mac

**Make scripts executable:**
```bash
chmod +x docker-*.sh
```

### Container is slow or unresponsive

**Increase Docker resources:**
- Open Docker Desktop → Settings → Resources
- Increase Memory to at least 8GB
- Increase CPUs to at least 4 cores

Or uncomment resource limits in `docker-compose.local.yml`:
```yaml
deploy:
  resources:
    limits:
      cpus: '4'
      memory: 8G
```

### Can't access Web UI

1. Check container is running: `docker ps`
2. Check logs: `docker logs agent-zero-local`
3. Verify port mapping: `docker port agent-zero-local`
4. Try accessing: `http://localhost:50080`
5. If using WSL2, try: `http://127.0.0.1:50080`

### Container exits immediately

**View exit logs:**
```bash
docker logs agent-zero-local
docker inspect agent-zero-local
```

**Common causes:**
- Port already in use
- Insufficient memory
- Volume mount path doesn't exist
- Base image not pulled

## 🔐 Security Notes

### Default SSH Access

The container has SSH enabled on port 55022 (mapped from container port 22) for development purposes.

**To set root password:**
1. Access Web UI → Settings → Development
2. Set "RFC Password" (Root password)
3. Save settings

**To connect via SSH:**
```bash
ssh root@localhost -p 55022
```

### Web UI Authentication

To enable authentication:

1. Access Web UI → Settings → Authentication
2. Set "UI Login" and "UI Password"
3. Save and restart container

Or set in `docker-compose.local.yml`:
```yaml
environment:
  - AUTH_LOGIN=admin
  - AUTH_PASSWORD=your-secure-password
```

## 📦 Building from Specific Git Branch

To build from a specific branch instead of local files:

```bash
cd docker/run

# From main branch
docker build -t agent-zero-main --build-arg BRANCH=main --build-arg CACHE_DATE=$(date +%Y-%m-%d:%H:%M:%S) .

# From development branch
docker build -t agent-zero-dev --build-arg BRANCH=development --build-arg CACHE_DATE=$(date +%Y-%m-%d:%H:%M:%S) .

# Run it
docker run -d --name agent-zero -p 50080:80 agent-zero-main
```

## 🔄 Updating Agent Zero

### Method 1: Rebuild (Recommended)

```bash
# Pull latest code
git pull

# Backup data via Web UI (Settings → Backup & Restore)

# Rebuild
docker-compose -f docker-compose.local.yml build --no-cache

# Restart
docker-compose -f docker-compose.local.yml up -d

# Restore data via Web UI if needed
```

### Method 2: Pull from DockerHub

```bash
# Stop local container
docker-compose -f docker-compose.local.yml down

# Pull official image
docker pull agent0ai/agent-zero:latest

# Run official image
docker run -d --name agent-zero-official -p 50080:80 agent0ai/agent-zero:latest
```

## 🎯 Advanced Usage

### Custom Dockerfile Modifications

To customize the Docker image:

1. Edit `DockerfileLocal`
2. Rebuild: `docker-compose -f docker-compose.local.yml build --no-cache`
3. Test your changes

### Multi-Architecture Build

Build for both AMD64 and ARM64:

```bash
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t agent-zero-local \
  -f DockerfileLocal \
  --build-arg CACHE_DATE=$(date +%Y-%m-%d:%H:%M:%S) \
  .
```

### Development Mode

For active development with hot-reload:

```bash
# Map entire project directory (not recommended for production)
docker run -d \
  --name agent-zero-dev \
  -p 50080:80 \
  -p 55022:22 \
  -v $(pwd):/a0 \
  agent-zero-local
```

**Note:** This allows live code editing but can cause upgrade issues.

## 📞 Support & Resources

- **Official Documentation**: [docs/README.md](docs/README.md)
- **GitHub Issues**: https://github.com/agent0ai/agent-zero/issues
- **Discord Community**: https://discord.gg/B8KZKNsPpj
- **Website**: https://agent-zero.ai

## 📄 License

This project is licensed under the terms specified in the [LICENSE](LICENSE) file.

---

**Happy Building! 🚀**

For more information, see the [main README](README.md) and [documentation](docs/README.md).



