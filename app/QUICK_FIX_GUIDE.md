# Quick Fix Guide - Portal Backend Issues

## Issue 1: 500 Error on `/api/user/agent-zero-status`

### Quick Diagnosis

```bash
# Run diagnostics
docker exec portal-backend-local python -m app.diagnostics

# Check logs
docker logs portal-backend-local --tail 50 | grep -i "agent zero status"
```

### Common Fixes

**1. Missing Environment Variables**
```bash
# Check if set
docker exec portal-backend-local printenv | grep SUPABASE

# If missing, update docker-compose.local.yml or .env file
```

**2. Database Connection Issue**
```bash
# Test connection
docker exec portal-backend-local python -c "from app.database import SupabaseDB; db = SupabaseDB.get_instance(); print('OK')"
```

**3. User Not Found (Normal)**
- If user doesn't exist in database, endpoint should return empty status
- If it returns 500, there's a database query issue

## Issue 2: CORS Error on `/api/user/connect-agent-zero`

### Quick Diagnosis

```bash
# Check CORS configuration
docker exec portal-backend-local printenv CORS_ORIGINS

# Test OPTIONS preflight
curl -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Content-Type,Authorization" \
     -X OPTIONS \
     http://localhost:5000/api/user/connect-agent-zero \
     -v
```

### Quick Fix

**1. Identify Frontend Origin**
- Check browser console/network tab
- Common origins:
  - `http://localhost:3000` (React default)
  - `http://localhost:5173` (Vite default)
  - `http://127.0.0.1:3000`

**2. Update CORS_ORIGINS**

Edit `docker-compose.local.yml`:
```yaml
environment:
  - CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173
```

**3. Restart Container**
```bash
docker-compose -f docker-compose.local.yml restart portal-backend
```

**4. Verify**
```bash
# Check CORS is enabled
docker logs portal-backend-local | grep -i cors

# Should see: "CORS enabled for origins: ..."
```

## Complete Troubleshooting Workflow

```bash
# 1. Run full diagnostics
docker exec portal-backend-local python -m app.diagnostics

# 2. Check environment
docker exec portal-backend-local printenv | grep -E "(SUPABASE|CORS)"

# 3. Check logs
docker logs portal-backend-local --tail 100

# 4. Test endpoints
curl -H "Authorization: Bearer <token>" \
     http://localhost:5000/api/user/agent-zero-status

# 5. Test CORS
curl -H "Origin: http://localhost:3000" \
     -X OPTIONS \
     http://localhost:5000/api/user/connect-agent-zero \
     -v
```

## Environment Variables Checklist

Required:
- ✅ `SUPABASE_URL`
- ✅ `SUPABASE_ANON_KEY`
- ✅ `SUPABASE_SERVICE_ROLE_KEY`

Optional (but recommended):
- ⚠️ `SUPABASE_JWT_SECRET` (falls back to anon key)
- ⚠️ `CORS_ORIGINS` (defaults to `http://localhost:3000`)
- ⚠️ `FLASK_DEBUG` (set to `True` for detailed errors)

## Still Having Issues?

1. **Check backend logs:**
   ```bash
   docker logs portal-backend-local --follow
   ```

2. **Enable debug mode:**
   ```yaml
   environment:
     - FLASK_DEBUG=True
   ```

3. **Test with curl:**
   ```bash
   # Get token from Supabase
   TOKEN="your-jwt-token"
   
   # Test status endpoint
   curl -H "Authorization: Bearer $TOKEN" \
        http://localhost:5000/api/user/agent-zero-status
   ```

4. **Review investigation report:**
   See `app/INVESTIGATION_REPORT.md` for detailed analysis.
