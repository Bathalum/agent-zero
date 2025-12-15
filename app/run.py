"""
Flask Application Entry Point

Run with: python -m app.run
Or: flask run
Or: gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.config import Config

# Validate configuration
try:
    Config.validate()
except ValueError as e:
    print(f"Configuration error: {e}", file=sys.stderr)
    print("Please set required environment variables. See app/env.example", file=sys.stderr)
    sys.exit(1)

app = create_app()

if __name__ == '__main__':
    import json
    from datetime import datetime
    
    # #region agent log
    DEBUG_LOG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.cursor', 'debug.log')
    def _debug_log(location, message, data=None, hypothesis_id=None):
        try:
            log_entry = {
                "id": f"log_{int(datetime.now().timestamp() * 1000)}",
                "timestamp": int(datetime.now().timestamp() * 1000),
                "location": location,
                "message": message,
                "data": data or {},
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": hypothesis_id
            }
            log_dir = os.path.dirname(DEBUG_LOG_PATH)
            os.makedirs(log_dir, exist_ok=True)
            with open(DEBUG_LOG_PATH, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception:
            pass
    # #endregion
    
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # #region agent log
    _debug_log("app/run.py:__main__", "Starting Flask server", {
        "port": port,
        "host": "0.0.0.0",
        "debug": debug
    }, "A")
    # #endregion
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
