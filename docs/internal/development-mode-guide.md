# 🔥 Development Mode - Hot Reload Guide

## ✅ Setup Complete!

Your Docker container is now configured for **development mode** with hot-reloading enabled!

## 📋 What's Configured

The following directories and files are **live-mounted** from your local machine into the Docker container:

### 📁 Directories (Live Updates)
- `./python` → `/a0/python` - All Python helper modules
- `./agents` → `/a0/agents` - Agent configurations
- `./prompts` → `/a0/prompts` - Prompt templates
- `./webui` → `/a0/webui` - Web UI files (HTML, CSS, JS)
- `./lib` → `/a0/lib` - Library files

### 📄 Individual Files (Live Updates)
- `./run_ui.py` - Web server entry point
- `./run_tunnel.py` - Tunnel server
- `./agent.py` - Main agent logic
- `./models.py` - Model configurations
- `./initialize.py` - Initialization code
- `./preload.py` - Preload scripts
- `./prepare.py` - Preparation scripts

## 🔄 How Hot-Reload Works

### Python Backend Changes
When you modify Python files (`.py`):
1. **Save the file** on your local machine
2. The change is **immediately reflected** in the container
3. Flask's auto-reload will **detect the change**
4. The server will **automatically restart** (takes ~2-3 seconds)
5. Refresh your browser to see the changes

**Example workflow:**
```python
# Edit python/helpers/settings.py locally
def my_new_function():
    return "Hello from hot-reload!"

# Save the file
# Flask detects the change and restarts
# New function is immediately available!
```

### Frontend Changes (Web UI)
When you modify web files (HTML, CSS, JS):
1. **Save the file** on your local machine
2. The change is **immediately reflected** in the container
3. **Refresh your browser** (Ctrl+F5 for hard refresh)
4. Changes appear instantly!

**Example workflow:**
```html
<!-- Edit webui/index.html locally -->
<h1>My Custom Title</h1>

<!-- Save → Refresh browser → See changes! -->
```

### Prompt Changes
When you modify prompts:
1. **Save the prompt file** locally
2. The change is **immediately available** in the container
3. Next agent interaction will use the **new prompt**

## ⚡ Quick Commands

### View Live Logs
```powershell
# Follow logs in real-time to see Flask reloading
docker logs agent-zero-local -f
```

### Restart Container (if needed)
```powershell
docker-compose -f docker-compose.local.yml restart
```

### Stop Container
```powershell
docker-compose -f docker-compose.local.yml down
```

### Start Container
```powershell
docker-compose -f docker-compose.local.yml up -d
```

### Access Container Shell
```powershell
docker exec -it agent-zero-local bash
```

## 🎯 What's NOT Hot-Reloaded

These changes **require a container restart** or **rebuild**:

### Container Restart Required
- Changes to `requirements.txt` (Python dependencies)
- Changes to environment variables in `docker-compose.local.yml`
- Changes to port mappings

### Full Rebuild Required
- Changes to `DockerfileLocal`
- Changes to system packages
- Changes to base image configuration

## 📊 Verify Hot-Reload is Working

### Test 1: Backend Change
1. Open `python/helpers/print_style.py`
2. Add a print statement
3. Save the file
4. Watch the logs: `docker logs agent-zero-local -f`
5. You should see Flask restarting

### Test 2: Frontend Change
1. Open `webui/index.html`
2. Change some visible text
3. Save the file
4. Refresh your browser (Ctrl+F5)
5. You should see the change immediately!

## 🚀 Development Workflow

```bash
# 1. Start your container (once)
docker-compose -f docker-compose.local.yml up -d

# 2. Make changes to your code locally
# Edit files in VS Code, your IDE, etc.

# 3. (Optional) Watch logs for auto-reload
docker logs agent-zero-local -f

# 4. Test your changes
# Open http://localhost:8080 and test

# 5. When done for the day
docker-compose -f docker-compose.local.yml down
```

## 🔍 Troubleshooting

### Changes Not Appearing?

**For Python files:**
- Check logs to see if Flask is restarting
- If not, manually restart: `docker-compose -f docker-compose.local.yml restart`
- Make sure you saved the file!

**For Web UI files:**
- Do a hard refresh: `Ctrl + Shift + R` or `Ctrl + F5`
- Clear browser cache if needed
- Check browser console for errors

### Flask Not Auto-Restarting?

Sometimes Flask's auto-reload can miss changes. If this happens:
```powershell
# Quick restart
docker-compose -f docker-compose.local.yml restart
```

### Volume Mount Issues?

If files aren't syncing:
```powershell
# Full restart
docker-compose -f docker-compose.local.yml down
docker-compose -f docker-compose.local.yml up -d
```

## 🎨 Best Practices

1. **Keep logs visible** while developing to catch errors quickly
2. **Save frequently** - changes are instant!
3. **Test incrementally** - make small changes and test
4. **Use hard refresh** for web UI changes
5. **Watch for Flask restarts** when modifying Python

## 📝 Current Configuration

**Container**: `agent-zero-local`  
**Web UI**: http://localhost:8080  
**SSH Access**: localhost:2222  
**Mode**: Development (Hot-Reload Enabled)  

**Volume Mounts**:
- ✅ Source code directories mounted
- ✅ Data directories persisted
- ✅ Live updates enabled
- ✅ Flask auto-reload active

---

## 🎉 You're All Set!

Start coding and see your changes instantly! No more rebuilding Docker images for every change.

**Happy developing! 🚀**

