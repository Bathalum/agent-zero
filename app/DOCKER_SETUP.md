# Portal Backend Docker Setup

The portal backend Flask app is now integrated into the Docker Compose setup.

## Services

When you run `docker-compose -f docker-compose.local.yml up -d`, two services start:

1. **agent-zero-local** - Agent Zero backend (port 8080)
2. **portal-backend-local** - Portal Flask backend (port 5000)

## Environment Variables

Set these in your `.env` file or export them before running docker-compose:

```bash
# Portal Backend
PORTAL_PORT=5000
FLASK_SECRET_KEY=your-secret-key
FLASK_DEBUG=False
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_JWT_SECRET=your-jwt-secret  # Optional

# Agent Zero (for portal backend to connect)
AGENT_ZERO_URL=http://agent-zero-local:80  # Internal Docker network
AGENT_ZERO_REQUEST_TIMEOUT=10
```

## Running

```bash
# Start both services
docker-compose -f docker-compose.local.yml up -d

# View logs
docker logs portal-backend-local -f

# Stop services
docker-compose -f docker-compose.local.yml down
```

## Development

The Flask app code is mounted as a volume for hot-reload:
- `./app:/app/app` - Code changes reflect immediately
- Restart container to pick up new dependencies

## Network

Both services are on the `agent-zero-network` bridge network:
- Portal backend can reach Agent Zero at `http://agent-zero-local:80`
- Frontend connects to portal backend at `http://localhost:5000`
