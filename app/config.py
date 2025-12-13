"""
Application Configuration

Production-ready configuration with environment variables.
"""

import os


class Config:
    """Base configuration"""
    
    # Flask
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', os.urandom(32).hex())
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # CORS - can be comma-separated string or list
    _cors_origins = os.getenv('CORS_ORIGINS', 'http://localhost:3000')
    CORS_ORIGINS = [origin.strip() for origin in _cors_origins.split(',') if origin.strip()]
    
    # Supabase Configuration
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')
    SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    SUPABASE_JWT_SECRET = os.getenv('SUPABASE_JWT_SECRET')  # Optional, falls back to anon key
    
    # Agent Zero Integration Configuration
    AGENT_ZERO_URL = os.getenv('AGENT_ZERO_URL', 'http://localhost:8080')
    AGENT_ZERO_REQUEST_TIMEOUT = int(os.getenv('AGENT_ZERO_REQUEST_TIMEOUT', '10'))
    
    @staticmethod
    def validate():
        """Validate required configuration."""
        required_vars = [
            'SUPABASE_URL',
            'SUPABASE_ANON_KEY',
            'SUPABASE_SERVICE_ROLE_KEY'
        ]
        missing = [var for var in required_vars if not os.getenv(var)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
