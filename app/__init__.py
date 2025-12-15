"""
Flask Application Factory

Production-ready Flask app with Supabase integration.
"""

from flask import Flask, request
from flask_cors import CORS
import os
import logging
import json
from datetime import datetime

from app.config import Config
from app.routes.agent_zero import agent_zero_bp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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


def create_app(config_class=Config):
    """Create and configure Flask application."""
    # #region agent log
    _debug_log("app/__init__.py:create_app", "Flask app creation started", {"config_class": str(config_class)}, "A")
    # #endregion
    
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Parse CORS origins from config
    cors_origins = app.config.get('CORS_ORIGINS', [])
    if isinstance(cors_origins, str):
        cors_origins = [origin.strip() for origin in cors_origins.split(',') if origin.strip()]
    
    # #region agent log
    _debug_log("app/__init__.py:create_app", "CORS origins parsed", {"cors_origins": cors_origins, "count": len(cors_origins)}, "B")
    # #endregion
    
    # CORS configuration
    CORS(app, resources={
        r"/api/*": {
            "origins": cors_origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })
    
    # #region agent log
    @app.before_request
    def log_request():
        if request.path.startswith('/api/'):
            origin = request.headers.get('Origin', 'none')
            _debug_log("app/__init__.py:before_request", "API request received", {
                "path": request.path,
                "method": request.method,
                "origin": origin,
                "origin_in_allowed": origin in cors_origins if origin != 'none' else False
            }, "B")
    # #endregion
    
    # Register blueprints
    app.register_blueprint(agent_zero_bp)
    
    # #region agent log
    port = int(os.getenv('PORT', 5000))
    _debug_log("app/__init__.py:create_app", "Flask app initialized", {
        "port": port,
        "blueprints_registered": [bp.name for bp in app.blueprints.values()],
        "cors_origins": cors_origins
    }, "A")
    # #endregion
    
    logger.info(f"Flask application initialized on port {os.getenv('PORT', 5000)}")
    logger.info(f"CORS enabled for origins: {', '.join(cors_origins)}")
    
    return app
