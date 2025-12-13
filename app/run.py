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
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
