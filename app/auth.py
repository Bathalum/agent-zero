"""
Authentication Middleware

Supabase JWT authentication for Flask routes.
"""

import os
import logging
from functools import wraps
from flask import request, g, jsonify
import jwt

logger = logging.getLogger(__name__)


class AuthError(Exception):
    """Authentication error."""
    pass


def verify_jwt_token(token: str) -> dict:
    """
    Verify Supabase JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload
        
    Raises:
        AuthError: If token is invalid
    """
    try:
        # Remove 'Bearer ' prefix if present
        if token.startswith('Bearer '):
            token = token[7:]
        
        # Get JWT secret from Supabase
        supabase_jwt_secret = os.getenv('SUPABASE_JWT_SECRET')
        if not supabase_jwt_secret:
            # Fallback: use anon key (less secure, but works for development)
            supabase_jwt_secret = os.getenv('SUPABASE_ANON_KEY')
        
        if not supabase_jwt_secret:
            raise AuthError("JWT secret not configured")
        
        # Decode and verify token
        payload = jwt.decode(
            token,
            supabase_jwt_secret,
            algorithms=['HS256'],
            audience='authenticated'
        )
        
        return payload
        
    except jwt.ExpiredSignatureError:
        raise AuthError("Token expired")
    except jwt.DecodeError as e:
        raise AuthError(f"Invalid token: {str(e)}")
    except jwt.InvalidTokenError as e:
        raise AuthError(f"Invalid token: {str(e)}")
    except Exception as e:
        logger.error(f"Error verifying token: {e}", exc_info=True)
        raise AuthError("Token verification failed")


def get_current_user():
    """
    Get current authenticated user from request.
    
    Returns:
        User object with 'id' attribute
        
    Raises:
        AuthError: If user is not authenticated
    """
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        raise AuthError("Authorization header required")
    
    try:
        payload = verify_jwt_token(auth_header)
        user_id = payload.get('sub')  # Supabase uses 'sub' for user ID
        
        if not user_id:
            raise AuthError("User ID not found in token")
        
        # Store user info in Flask g
        g.user = {
            'id': user_id,
            'email': payload.get('email'),
            'payload': payload
        }
        
        return g.user
        
    except AuthError:
        raise
    except Exception as e:
        logger.error(f"Error getting current user: {e}", exc_info=True)
        raise AuthError("Authentication failed")


def require_auth(f):
    """
    Decorator to require authentication for a route.
    
    Usage:
        @agent_zero_bp.route('/api/user/status')
        @require_auth
        def get_status():
            user = g.user
            # ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            get_current_user()
            return f(*args, **kwargs)
        except AuthError as e:
            return jsonify({'error': str(e)}), 401
        except Exception as e:
            logger.error(f"Auth error: {e}", exc_info=True)
            return jsonify({'error': 'Authentication failed'}), 401
    
    return decorated_function
