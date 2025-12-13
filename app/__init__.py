"""
Flask Application Factory

Production-ready Flask app with Supabase integration.
"""

from flask import Flask
from flask_cors import CORS
import os
import logging

from app.config import Config
from app.routes.agent_zero import agent_zero_bp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app(config_class=Config):
    """Create and configure Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Parse CORS origins from config
    cors_origins = app.config.get('CORS_ORIGINS', [])
    if isinstance(cors_origins, str):
        cors_origins = [origin.strip() for origin in cors_origins.split(',') if origin.strip()]
    
    # CORS configuration
    CORS(app, resources={
        r"/api/*": {
            "origins": cors_origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })
    
    # Register blueprints
    app.register_blueprint(agent_zero_bp)
    
    logger.info(f"Flask application initialized on port {os.getenv('PORT', 5000)}")
    logger.info(f"CORS enabled for origins: {', '.join(cors_origins)}")
    
    return app
