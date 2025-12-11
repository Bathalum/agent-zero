# CORS Setup for Microservices Architecture

This document describes how to configure CORS (Cross-Origin Resource Sharing) for Agent Zero API to enable separated frontend (Vercel) and backend (AWS) architecture.

## Overview

Agent Zero supports CORS to allow external frontend applications to communicate with the API. This enables a microservices architecture where:

- **Frontend**: Deployed on Vercel (or any CDN)
- **Backend**: Agent Zero API deployed on AWS (or any cloud provider)

## Configuration

### Environment Variable

CORS is configured via the `CORS_ALLOWED_ORIGINS` environment variable:

```bash
CORS_ALLOWED_ORIGINS=https://app.vercel.app,https://yourdomain.com
```

**Format**: Comma-separated list of allowed origins (no spaces around commas)

### Development Mode

In development mode (when not dockerized), CORS automatically allows these local origins:

- `http://localhost:3000`
- `http://localhost:5173`
- `http://127.0.0.1:3000`
- `http://127.0.0.1:5173`

No configuration needed for local development!

### Production Mode

In production (dockerized), you **must** set `CORS_ALLOWED_ORIGINS` environment variable. If not set, CORS will be disabled for security.

## Docker Setup

### docker-compose.local.yml

Add the environment variable:

```yaml
environment:
  - TZ=UTC
  - CORS_ALLOWED_ORIGINS=https://app.vercel.app,https://yourdomain.com
```

### AWS ECS Task Definition

Add to environment variables:

```json
{
  "name": "CORS_ALLOWED_ORIGINS",
  "value": "https://app.vercel.app,https://yourdomain.com"
}
```

## API Authentication

All API endpoints require authentication via API key:

```javascript
fetch('https://api.argent.com/api/profile_list', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-KEY': 'your-api-key-here'
  },
  body: JSON.stringify({})
})
```

### Getting Your API Key

1. Open Agent Zero settings
2. Navigate to "External Services" tab
3. Find "MCP Server Token" - this is your API key
4. Copy and use it in your frontend

## Security Considerations

### Origin Whitelisting

- **Never use wildcards** (`*`) in production
- Only whitelist your specific domains
- Use HTTPS origins in production

### API Key Security

- Store API keys securely (environment variables, secrets manager)
- Never commit API keys to version control
- Rotate keys periodically
- Use different keys for development and production

### HTTPS Only

- Always use HTTPS in production
- CORS origins should use `https://` protocol
- Configure AWS ALB/CloudFront for SSL termination

## Testing

### Local Testing

1. Start your frontend locally (e.g., `npm run dev` on port 3000)
2. Start Agent Zero:
   ```powershell
   docker-compose -f docker-compose.local.yml up -d
   ```
3. Test API call:
   ```javascript
   fetch('http://localhost:8080/api/profile_list', {
     method: 'POST',
     headers: {
       'Content-Type': 'application/json',
       'X-API-KEY': 'your-api-key'
     },
     body: JSON.stringify({})
   })
   ```

### Production Testing

1. Set `CORS_ALLOWED_ORIGINS` in your deployment environment
2. Verify CORS headers in browser DevTools:
   - Open Network tab
   - Check response headers for:
     - `Access-Control-Allow-Origin`
     - `Access-Control-Allow-Methods`
     - `Access-Control-Allow-Headers`
3. Test API calls from your Vercel frontend

## Troubleshooting

### CORS Error: "No 'Access-Control-Allow-Origin' header"

**Cause**: Origin not whitelisted or CORS not configured

**Solution**:
1. Check `CORS_ALLOWED_ORIGINS` environment variable is set
2. Verify your frontend URL matches exactly (including protocol)
3. Check Agent Zero logs for CORS configuration messages

### 401 Unauthorized

**Cause**: Missing or invalid API key

**Solution**:
1. Ensure `X-API-KEY` header is included in request
2. Verify API key matches MCP Server Token in settings
3. Check API key is not expired or rotated

### CSRF Token Error

**Cause**: CSRF protection blocking request

**Solution**:
- API routes with `X-API-KEY` header bypass CSRF automatically
- Ensure you're using API key authentication, not session-based auth

## Security Headers

Agent Zero automatically adds security headers in production:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `X-Robots-Tag: noindex, nofollow`

## Architecture Example

```
┌─────────────────────────────────────┐
│   Vercel Frontend                    │
│   https://app.vercel.app            │
└──────────────┬──────────────────────┘
               │ HTTPS + CORS
               │ X-API-KEY header
               ▼
┌─────────────────────────────────────┐
│   AWS Application Load Balancer      │
│   (HTTPS termination)                │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   AWS ECS/Fargate (Agent Zero)      │
│   - CORS enabled                    │
│   - API key validation              │
│   - Security headers                │
└─────────────────────────────────────┘
```

## Best Practices

1. **Use Environment Variables**: Never hardcode origins in code
2. **Separate Dev/Prod**: Use different API keys for development and production
3. **Monitor Access**: Log API access and monitor for suspicious activity
4. **Rate Limiting**: Consider adding rate limiting for production (future enhancement)
5. **API Versioning**: Use `/api/v1/...` for future API versioning

## Related Documentation

- [API Documentation](./instruments.md)
- [Profile System Architecture](../developer/profile-system-architecture.md)
- [Development Mode Guide](../internal/development-mode-guide.md)

