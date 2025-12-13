# Portal Backend - Agent Zero Integration

Production-ready Flask backend with Supabase integration for Agent Zero API key management.

## Quick Start with Docker

The easiest way to run the portal backend is via Docker Compose (see `DOCKER_SETUP.md`):

```bash
# Set environment variables in .env file
# Then start services
docker-compose -f docker-compose.local.yml up -d

# Portal backend will be available at http://localhost:5000
```

## Manual Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp app/.env.example app/.env
```

Required variables:
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_ANON_KEY` - Supabase anonymous key
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key (for backend operations)
- `AGENT_ZERO_URL` - Agent Zero backend URL (default: http://localhost:8080)

### 3. Database Migration

Run the migration to add Agent Zero fields to your Supabase `users` table:

```sql
-- Run this in Supabase SQL Editor
ALTER TABLE users 
ADD COLUMN agent_zero_api_key VARCHAR(255),
ADD COLUMN agent_zero_url VARCHAR(255) DEFAULT 'http://localhost:8080',
ADD COLUMN agent_zero_api_key_retrieved_at TIMESTAMP,
ADD COLUMN agent_zero_instance_id VARCHAR(255);

CREATE INDEX idx_users_agent_zero_api_key ON users(agent_zero_api_key) WHERE agent_zero_api_key IS NOT NULL;
```

### 4. Run the Application

```bash
# Development
python -m app.run

# Or with Flask CLI
export FLASK_APP=app
flask run

# Production (with gunicorn)
gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"
```

## API Endpoints

### GET /api/user/agent-zero-status

Get Agent Zero API key status for the current user.

**Headers:**
```
Authorization: Bearer <supabase-jwt-token>
```

**Response:**
```json
{
  "has_api_key": true,
  "agent_zero_url": "http://localhost:8080",
  "api_key_retrieved_at": "2025-01-08T12:34:56.789Z"
}
```

### POST /api/user/get-agent-zero-api-key

Retrieve and store Agent Zero API key for the current user.

**Headers:**
```
Authorization: Bearer <supabase-jwt-token>
Content-Type: application/json
```

**Request Body (optional):**
```json
{
  "agent_zero_url": "http://localhost:8080"
}
```

**Response:**
```json
{
  "success": true,
  "message": "API key retrieved and stored successfully",
  "api_key": "abc123xyz..."
}
```

## Architecture

- **Flask App** (`app/__init__.py`) - Application factory
- **Supabase Integration** (`app/database.py`) - Database operations
- **Authentication** (`app/auth.py`) - JWT token verification
- **Agent Zero Client** (`app/services/agent_zero_client.py`) - Agent Zero API client
- **Routes** (`app/routes/agent_zero.py`) - API endpoints

## Security

- JWT authentication via Supabase
- Service role key used only for backend operations
- API keys stored encrypted in Supabase
- SSRF protection (URL validation)
- CORS configured for frontend origins

## Production Deployment

1. Set all environment variables
2. Use production WSGI server (gunicorn/uwsgi)
3. Enable HTTPS
4. Configure proper CORS origins
5. Set up monitoring and logging
6. Use Supabase Row Level Security (RLS) for additional security
