# Docker Compose Commands Reference

## Important Notes

- **Service name**: `portal-backend` (used in docker-compose commands)
- **Container name**: `portal-backend-local` (used in docker commands)
- The `version: '3.8'` line has been removed as it's obsolete in newer docker-compose versions

## Common Commands

### View Logs
```bash
# Using service name (recommended)
docker-compose -f docker-compose.local.yml logs -f portal-backend

# Or using container name with docker directly
docker logs -f portal-backend-local
```

### Rebuild Containers (After Requirements Update)
```bash
# Stop containers
docker-compose -f docker-compose.local.yml down

# Rebuild without cache to ensure new dependencies are installed
docker-compose -f docker-compose.local.yml build --no-cache portal-backend

# Start containers
docker-compose -f docker-compose.local.yml up -d
```

### Restart Services
```bash
docker-compose -f docker-compose.local.yml restart
```

### View All Services
```bash
docker-compose -f docker-compose.local.yml ps
```

### View Logs for Both Services
```bash
docker-compose -f docker-compose.local.yml logs -f
```

### Stop All Services
```bash
docker-compose -f docker-compose.local.yml down
```

### Start All Services
```bash
docker-compose -f docker-compose.local.yml up -d
```
