"""
Agent Zero Integration Routes

Flask routes for managing Agent Zero API key retrieval and status.
"""

import logging
import json
import os
from datetime import datetime
from flask import Blueprint, request, jsonify, g

from app.services.agent_zero_client import (
    get_api_key_from_agent_zero,
    authenticate_with_credentials,
    set_settings,
    get_initial_agent_zero_credentials,
    AgentZeroConnectionError,
    AgentZeroAuthenticationError,
    AgentZeroAPIKeyNotFoundError,
    AgentZeroClientError
)
from app.database import SupabaseDB
from app.auth import require_auth
from app.config import Config

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

# Create blueprint
agent_zero_bp = Blueprint('agent_zero', __name__)


@agent_zero_bp.route('/api/user/initialize-profile', methods=['POST'])
@require_auth
def initialize_user_profile():
    """
    Initialize user profile in account_users table.
    
    This endpoint ensures the authenticated user has a record in account_users,
    solving the chicken-egg problem where users exist in auth.users but not
    in account_users until they connect to Agent Zero.
    
    Returns:
        JSON response:
        {
            "success": boolean,
            "message": string,
            "user_id": string
        }
    """
    try:
        user = g.user
        db = SupabaseDB.get_instance()
        
        # Ensure user exists in account_users (creates if doesn't exist)
        user_record = db.ensure_user_exists(user['id'], user.get('email'))
        
        logger.info(f"User profile initialized for user {user['id']}")
        
        return jsonify({
            "success": True,
            "message": "User profile initialized successfully",
            "user_id": user['id']
        }), 200
        
    except Exception as e:
        logger.error(f"Error initializing user profile for user {user.get('id', 'unknown')}: {e}", exc_info=True)
        
        # In debug mode, include more error details
        error_response = {
            "success": False,
            "message": "Failed to initialize user profile"
        }
        
        # Include detailed error in development mode
        if Config.DEBUG:
            error_response["details"] = str(e)
            error_response["error_type"] = type(e).__name__
        
        return jsonify(error_response), 500


@agent_zero_bp.route('/api/user/agent-zero-status', methods=['GET'])
@require_auth
def get_agent_zero_status():
    """
    Get Agent Zero API key status for the current user.
    
    Returns:
        JSON response with status information:
        {
            "has_api_key": boolean,
            "agent_zero_url": string (stored URL for display/reference only),
            "configured_url": string (actual URL used for connections from AGENT_ZERO_URL env var),
            "api_key_retrieved_at": timestamp or null
        }
    """
    try:
        user = g.user
        db = SupabaseDB.get_instance()
        
        # Get user's Agent Zero status from Supabase
        status = db.get_user_agent_zero_status(user['id'])
        
        # Add configured URL for reference (this is what's actually used for connections)
        status['configured_url'] = Config.AGENT_ZERO_URL
        # Note: status['agent_zero_url'] is the stored URL (for display/reference only)
        
        return jsonify(status), 200
        
    except Exception as e:
        logger.error(f"Error getting Agent Zero status for user {user.get('id', 'unknown')}: {e}", exc_info=True)
        
        # In debug mode, include more error details
        error_response = {
            "error": "Failed to retrieve Agent Zero status"
        }
        
        # Include detailed error in development mode
        if Config.DEBUG:
            error_response["details"] = str(e)
            error_response["error_type"] = type(e).__name__
        
        return jsonify(error_response), 500


@agent_zero_bp.route('/api/user/agent-zero-credentials', methods=['GET'])
@require_auth
def get_agent_zero_credentials():
    """
    Get Agent Zero credentials for the current user.
    
    Returns:
        JSON response with credentials:
        {
            "username": string,
            "password": string,
            "agent_zero_url": string
        }
    """
    try:
        user = g.user
        db = SupabaseDB.get_instance()
        
        # Get user's Agent Zero credentials from Supabase
        credentials = db.get_agent_zero_credentials(user['id'])
        
        if not credentials:
            return jsonify({
                "error": "Agent Zero credentials not found"
            }), 404
        
        return jsonify(credentials), 200
        
    except Exception as e:
        logger.error(f"Error getting Agent Zero credentials for user {user.get('id', 'unknown')}: {e}", exc_info=True)
        
        # In debug mode, include more error details
        error_response = {
            "error": "Failed to retrieve Agent Zero credentials"
        }
        
        # Include detailed error in development mode
        if Config.DEBUG:
            error_response["details"] = str(e)
            error_response["error_type"] = type(e).__name__
        
        return jsonify(error_response), 500


@agent_zero_bp.route('/api/user/agent-zero-initial-credentials', methods=['GET'])
@require_auth
def get_initial_agent_zero_credentials_endpoint():
    """
    Get initial Agent Zero credentials from Agent Zero settings (if accessible).
    
    Attempts to fetch credentials without authentication. If Agent Zero requires
    authentication, returns empty response indicating user must enter credentials manually.
    
    Returns:
        JSON response:
        {
            "username": string or null,
            "password": null (always null),
            "available": boolean
        }
    """
    try:
        user = g.user
        
        # Always use configured URL for connections (ensures correct Docker service name)
        agent_zero_url = Config.AGENT_ZERO_URL
        
        timeout = Config.AGENT_ZERO_REQUEST_TIMEOUT
        
        # Try to get initial credentials from Agent Zero
        logger.debug(f"Attempting to get initial credentials from {agent_zero_url}")
        credentials = get_initial_agent_zero_credentials(agent_zero_url, timeout)
        
        if credentials and credentials.get('username'):
            logger.info(f"Retrieved initial credentials for user {user['id']}")
            return jsonify({
                "username": credentials['username'],
                "password": None,  # Always None - user must enter manually
                "available": True
            }), 200
        else:
            # Agent Zero requires authentication or credentials not found
            return jsonify({
                "username": None,
                "password": None,
                "available": False,
                "message": "Agent Zero requires authentication. Please enter credentials manually."
            }), 200
        
    except Exception as e:
        logger.error(f"Error getting initial credentials for user {user.get('id', 'unknown')}: {e}", exc_info=True)
        
        # Return empty response on error (best-effort endpoint)
        return jsonify({
            "username": None,
            "password": None,
            "available": False,
            "message": "Unable to retrieve initial credentials"
        }), 200


@agent_zero_bp.route('/api/user/agent-zero-credentials', methods=['DELETE'])
@require_auth
def delete_agent_zero_credentials():
    """
    Clear Agent Zero credentials and API key for the current user.
    
    Returns:
        JSON response:
        {
            "success": boolean,
            "message": string
        }
    """
    try:
        user = g.user
        db = SupabaseDB.get_instance()
        
        # Clear credentials and API key from database
        result = db.clear_agent_zero_credentials(user['id'])
        
        # If user not found, still return success (idempotent operation)
        if not result:
            logger.warning(f"User {user['id']} not found when clearing credentials, but returning success")
        
        logger.info(f"Cleared Agent Zero credentials for user {user['id']}")
        
        return jsonify({
            "success": True,
            "message": "Agent Zero credentials and API key cleared successfully"
        }), 200
        
    except Exception as e:
        logger.error(f"Error clearing Agent Zero credentials for user {user.get('id', 'unknown')}: {e}", exc_info=True)
        
        # In debug mode, include more error details
        error_response = {
            "success": False,
            "message": "Failed to clear Agent Zero credentials"
        }
        
        # Include detailed error in development mode
        if Config.DEBUG:
            error_response["details"] = str(e)
            error_response["error_type"] = type(e).__name__
        
        return jsonify(error_response), 500


@agent_zero_bp.route('/api/user/agent-zero-credentials', methods=['PUT'])
@require_auth
def update_agent_zero_credentials():
    """
    Update Agent Zero credentials and automatically retrieve new API key.
    
    This endpoint:
    1. Updates Agent Zero's .env file via settings API (using old API key)
    2. Updates Portal Backend stored credentials
    3. Authenticates with new credentials
    4. Retrieves new API key (which changes when credentials change)
    5. Stores new API key
    
    Request Body:
        {
            "username": "newusername",
            "password": "newpassword",
            "agent_zero_url": "http://localhost:8080"  // Optional
        }
    
    Returns:
        JSON response:
        {
            "success": boolean,
            "message": string,
            "api_key": string (only if success)
        }
    """
    try:
        user = g.user
        db = SupabaseDB.get_instance()
        
        # Get request data
        request_data = request.get_json() or {}
        # Frontend-provided URL is stored for display/reference only
        frontend_url = request_data.get('agent_zero_url')
        # Always use configured URL for actual connections (ensures correct Docker service name)
        agent_zero_url = Config.AGENT_ZERO_URL
        username = request_data.get('username')
        password = request_data.get('password')
        
        # Validate input
        if not username or not password:
            return jsonify({
                "success": False,
                "message": "Username and password are required"
            }), 400
        
        # Validate frontend URL if provided (for storage)
        if frontend_url and not frontend_url.startswith(('http://', 'https://')):
            return jsonify({
                "success": False,
                "message": "Invalid Agent Zero URL"
            }), 400
        
        # Get user's stored API key (old API key needed to update settings)
        user_record = db.get_user_by_id(user['id'])
        if not user_record or not user_record.get('agent_zero_api_key'):
            return jsonify({
                "success": False,
                "message": "Agent Zero API key not found. Please connect to Agent Zero first."
            }), 404
        
        old_api_key = user_record['agent_zero_api_key']
        timeout = Config.AGENT_ZERO_REQUEST_TIMEOUT
        
        # Step 1: Update Agent Zero's .env file via settings API (using old API key)
        # Always use configured URL for connections (ensures correct Docker service name)
        try:
            logger.info(f"Updating Agent Zero credentials for user {user['id']} at {agent_zero_url}")
            set_settings(
                agent_zero_url=agent_zero_url,
                api_key=old_api_key,
                settings_data={
                    'auth_login': username,
                    'auth_password': password
                },
                timeout=timeout
            )
            logger.info(f"Agent Zero .env file updated for user {user['id']}")
        except AgentZeroConnectionError as e:
            logger.error(f"Connection error updating Agent Zero settings for user {user['id']} at {agent_zero_url}: {e}")
            error_msg = f"Unable to connect to Agent Zero at {agent_zero_url}. Please ensure it's running and the AGENT_ZERO_URL environment variable is correctly configured."
            if Config.DEBUG:
                error_msg += f" Error: {str(e)}"
            return jsonify({
                "success": False,
                "message": error_msg
            }), 503
        except AgentZeroAuthenticationError as e:
            logger.error(f"Authentication error updating Agent Zero settings for user {user['id']} at {agent_zero_url}: {e}")
            return jsonify({
                "success": False,
                "message": f"Authentication failed with stored API key: {str(e)}. Please reconnect to Agent Zero."
            }), 401
        except AgentZeroClientError as e:
            logger.error(f"Client error updating Agent Zero settings for user {user['id']} at {agent_zero_url}: {e}")
            error_msg = f"Error updating Agent Zero settings: {str(e)}"
            if Config.DEBUG:
                error_msg += f" (URL: {agent_zero_url})"
            return jsonify({
                "success": False,
                "message": error_msg
            }), 500
        
        # Step 2: Update Portal Backend stored credentials (use frontend URL if provided for display)
        try:
            db.store_agent_zero_credentials(
                user_id=user['id'],
                username=username,
                password=password,
                agent_zero_url=frontend_url or agent_zero_url,  # Store frontend URL for display
                email=user.get('email')
            )
            logger.info(f"Updated Portal Backend credentials for user {user['id']}")
        except Exception as e:
            logger.error(f"Error updating Portal Backend credentials for user {user['id']}: {e}", exc_info=True)
            return jsonify({
                "success": False,
                "message": "Failed to update stored credentials"
            }), 500
        
        # Step 3: Authenticate with new credentials (always use configured URL)
        try:
            auth_result = authenticate_with_credentials(
                agent_zero_url=agent_zero_url,
                username=username,
                password=password,
                timeout=timeout
            )
        except AgentZeroConnectionError as e:
            logger.error(f"Connection error authenticating with new credentials for user {user['id']} at {agent_zero_url}: {e}")
            error_msg = f"Unable to connect to Agent Zero at {agent_zero_url}. Please ensure it's running and the AGENT_ZERO_URL environment variable is correctly configured."
            if Config.DEBUG:
                error_msg += f" Error: {str(e)}"
            return jsonify({
                "success": False,
                "message": error_msg
            }), 503
        except AgentZeroAuthenticationError as e:
            logger.error(f"Authentication error with new credentials for user {user['id']} at {agent_zero_url}: {e}")
            return jsonify({
                "success": False,
                "message": f"Authentication failed with new credentials: {str(e)}"
            }), 401
        
        # Step 4: Retrieve new API key (which changed when credentials changed)
        try:
            new_api_key = get_api_key_from_agent_zero(
                agent_zero_url=agent_zero_url,
                timeout=timeout,
                session_cookies=auth_result['session_cookies'],
                csrf_token=auth_result['csrf_token']
            )
        except AgentZeroAPIKeyNotFoundError as e:
            logger.error(f"API key not found after credential update for user {user['id']}: {e}")
            return jsonify({
                "success": False,
                "message": "API key not found in Agent Zero settings."
            }), 404
        except AgentZeroClientError as e:
            logger.error(f"Client error retrieving new API key for user {user['id']}: {e}")
            return jsonify({
                "success": False,
                "message": f"Error retrieving new API key: {str(e)}"
            }), 500
        
        # Step 5: Store new API key (use frontend URL if provided for display)
        try:
            db.update_user_agent_zero_config(
                user_id=user['id'],
                api_key=new_api_key,
                agent_zero_url=frontend_url or agent_zero_url  # Store frontend URL for display
            )
            logger.info(f"Successfully updated credentials and API key for user {user['id']}")
            
            return jsonify({
                "success": True,
                "message": "Credentials updated successfully. New API key retrieved.",
                "api_key": new_api_key
            }), 200
            
        except Exception as e:
            logger.error(f"Database error storing new API key for user {user['id']}: {e}", exc_info=True)
            return jsonify({
                "success": False,
                "message": "Failed to store new API key."
            }), 500
        
    except Exception as e:
        logger.error(f"Unexpected error updating credentials: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "message": "An unexpected error occurred"
        }), 500


@agent_zero_bp.route('/api/user/connect-agent-zero', methods=['POST'])
@require_auth
def connect_agent_zero():
    """
    Connect to Agent Zero instance by storing credentials and retrieving API key.
    
    Request Body:
        {
            "agent_zero_url": "http://localhost:8080",
            "username": "user",
            "password": "pass"
        }
    
    Returns:
        JSON response:
        {
            "success": boolean,
            "message": string,
            "api_key": string (only if success)
        }
    """
    # #region agent log
    _debug_log("app/routes/agent_zero.py:connect_agent_zero", "Endpoint called", {
        "method": request.method,
        "has_user": hasattr(g, 'user'),
        "user_id": g.user.get('id') if hasattr(g, 'user') else None
    }, "A")
    # #endregion
    
    try:
        user = g.user
        db = SupabaseDB.get_instance()
        
        # #region agent log
        _debug_log("app/routes/agent_zero.py:connect_agent_zero", "Database instance obtained", {
            "db_exists": db is not None,
            "user_id": user['id']
        }, "C")
        # #endregion
        
        # Get request data
        request_data = request.get_json() or {}
        # Frontend-provided URL is stored for display/reference only
        frontend_url = request_data.get('agent_zero_url')
        # Always use configured URL for actual connections (ensures correct Docker service name)
        agent_zero_url = Config.AGENT_ZERO_URL
        username = request_data.get('username')
        password = request_data.get('password')
        
        # #region agent log
        _debug_log("app/routes/agent_zero.py:connect_agent_zero", "Request data parsed", {
            "has_username": bool(username),
            "has_password": bool(password),
            "frontend_url": frontend_url,
            "agent_zero_url_used": agent_zero_url
        }, "E")
        # #endregion
        
        # Validate input
        if not username or not password:
            return jsonify({
                "success": False,
                "message": "Username and password are required"
            }), 400
        
        # Validate frontend URL if provided (for storage)
        if frontend_url and not frontend_url.startswith(('http://', 'https://')):
            return jsonify({
                "success": False,
                "message": "Invalid Agent Zero URL"
            }), 400
        
        timeout = Config.AGENT_ZERO_REQUEST_TIMEOUT
        
        # Store credentials in database (use frontend URL if provided, otherwise configured URL)
        try:
            # #region agent log
            _debug_log("app/routes/agent_zero.py:connect_agent_zero", "Calling store_agent_zero_credentials", {
                "user_id": user['id'],
                "username": username,
                "has_email": 'email' in user,
                "user_email": user.get('email')
            }, "B")
            # #endregion
            db.store_agent_zero_credentials(
                user_id=user['id'],
                username=username,
                password=password,
                agent_zero_url=frontend_url or agent_zero_url,  # Store frontend URL for display
                email=user.get('email')
            )
            # #region agent log
            _debug_log("app/routes/agent_zero.py:connect_agent_zero", "store_agent_zero_credentials succeeded", {
                "user_id": user['id']
            }, "E")
            # #endregion
            logger.info(f"Stored credentials for user {user['id']}")
        except Exception as e:
            # #region agent log
            _debug_log("app/routes/agent_zero.py:connect_agent_zero", "store_agent_zero_credentials failed", {
                "user_id": user['id'],
                "error_type": type(e).__name__,
                "error_message": str(e),
                "is_value_error": isinstance(e, ValueError),
                "contains_migration": "migration required" in str(e).lower()
            }, "E")
            # #endregion
            logger.error(f"Error storing credentials for user {user['id']}: {e}", exc_info=True)
            
            # Provide helpful error message for missing migration
            error_message = "Failed to store credentials"
            if isinstance(e, ValueError) and "migration required" in str(e).lower():
                error_message = str(e)
            elif Config.DEBUG:
                error_message += f": {str(e)}"
            
            return jsonify({
                "success": False,
                "message": error_message
            }), 500
        
        # Authenticate with Agent Zero and retrieve API key
        # Always use configured URL for connections (ensures correct Docker service name)
        try:
            logger.info(f"Connecting to Agent Zero at {agent_zero_url} for user {user['id']}")
            auth_result = authenticate_with_credentials(
                agent_zero_url=agent_zero_url,
                username=username,
                password=password,
                timeout=timeout
            )
            
            # Retrieve API key using authenticated session
            api_key = get_api_key_from_agent_zero(
                agent_zero_url=agent_zero_url,
                timeout=timeout,
                session_cookies=auth_result['session_cookies'],
                csrf_token=auth_result['csrf_token']
            )
            
        except AgentZeroConnectionError as e:
            logger.error(f"Connection error for user {user['id']} to {agent_zero_url}: {e}")
            error_msg = f"Unable to connect to Agent Zero at {agent_zero_url}. Please ensure it's running and the AGENT_ZERO_URL environment variable is correctly configured."
            if Config.DEBUG:
                error_msg += f" Error: {str(e)}"
            return jsonify({
                "success": False,
                "message": error_msg
            }), 503
        except AgentZeroAuthenticationError as e:
            logger.error(f"Authentication error for user {user['id']} at {agent_zero_url}: {e}")
            error_msg = f"Authentication failed: {str(e)}"
            if Config.DEBUG:
                error_msg += f" (URL: {agent_zero_url})"
            return jsonify({
                "success": False,
                "message": error_msg
            }), 401
        except AgentZeroAPIKeyNotFoundError as e:
            logger.error(f"API key not found for user {user['id']} at {agent_zero_url}: {e}")
            return jsonify({
                "success": False,
                "message": "API key not found in Agent Zero settings."
            }), 404
        except AgentZeroClientError as e:
            logger.error(f"Client error for user {user['id']} at {agent_zero_url}: {e}")
            error_msg = f"Error retrieving API key: {str(e)}"
            if Config.DEBUG:
                error_msg += f" (URL: {agent_zero_url})"
            return jsonify({
                "success": False,
                "message": error_msg
            }), 500
        
        # Store API key in database (use frontend URL if provided for display, otherwise configured URL)
        try:
            db.update_user_agent_zero_config(
                user_id=user['id'],
                api_key=api_key,
                agent_zero_url=frontend_url or agent_zero_url  # Store frontend URL for display
            )
            
            logger.info(f"Successfully connected Agent Zero for user {user['id']}")
            
            return jsonify({
                "success": True,
                "message": "Successfully connected to Agent Zero and retrieved API key",
                "api_key": api_key
            }), 200
            
        except Exception as e:
            logger.error(f"Database error storing API key for user {user['id']}: {e}", exc_info=True)
            return jsonify({
                "success": False,
                "message": "Failed to store API key."
            }), 500
        
    except Exception as e:
        logger.error(f"Unexpected error connecting Agent Zero: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "message": "An unexpected error occurred"
        }), 500


@agent_zero_bp.route('/api/user/update-agent-zero-settings', methods=['POST'])
@require_auth
def update_agent_zero_settings():
    """
    Update Agent Zero settings using stored API key.
    
    Request Body:
        {
            "settings": {
                "api_key_openrouter": "sk-...",
                "chat_model_name": "openai/gpt-4",
                ...
            }
        }
    
    Returns:
        JSON response:
        {
            "success": boolean,
            "message": string
        }
    """
    try:
        user = g.user
        db = SupabaseDB.get_instance()
        
        # Get request data
        request_data = request.get_json() or {}
        settings_data = request_data.get('settings')
        
        if not settings_data or not isinstance(settings_data, dict):
            return jsonify({
                "success": False,
                "message": "Settings object is required"
            }), 400
        
        # Get user's stored API key
        user_record = db.get_user_by_id(user['id'])
        if not user_record or not user_record.get('agent_zero_api_key'):
            return jsonify({
                "success": False,
                "message": "Agent Zero API key not found. Please connect to Agent Zero first."
            }), 404
        
        api_key = user_record['agent_zero_api_key']
        # Always use configured URL for connections (ensures correct Docker service name)
        agent_zero_url = Config.AGENT_ZERO_URL
        
        timeout = Config.AGENT_ZERO_REQUEST_TIMEOUT
        
        # Update settings in Agent Zero
        try:
            logger.info(f"Updating Agent Zero settings for user {user['id']} at {agent_zero_url}")
            set_settings(
                agent_zero_url=agent_zero_url,
                api_key=api_key,
                settings_data=settings_data,
                timeout=timeout
            )
            
            logger.info(f"Updated Agent Zero settings for user {user['id']}")
            
            return jsonify({
                "success": True,
                "message": "Settings updated successfully"
            }), 200
            
        except AgentZeroConnectionError as e:
            logger.error(f"Connection error for user {user['id']} at {agent_zero_url}: {e}")
            error_msg = f"Unable to connect to Agent Zero at {agent_zero_url}. Please ensure it's running and the AGENT_ZERO_URL environment variable is correctly configured."
            if Config.DEBUG:
                error_msg += f" Error: {str(e)}"
            return jsonify({
                "success": False,
                "message": error_msg
            }), 503
        except AgentZeroAuthenticationError as e:
            logger.error(f"Authentication error for user {user['id']} at {agent_zero_url}: {e}")
            return jsonify({
                "success": False,
                "message": f"Authentication failed: {str(e)}. Please reconnect to Agent Zero."
            }), 401
        except AgentZeroClientError as e:
            logger.error(f"Client error for user {user['id']} at {agent_zero_url}: {e}")
            error_msg = f"Error updating settings: {str(e)}"
            if Config.DEBUG:
                error_msg += f" (URL: {agent_zero_url})"
            return jsonify({
                "success": False,
                "message": error_msg
            }), 500
        
    except Exception as e:
        logger.error(f"Unexpected error updating settings: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "message": "An unexpected error occurred"
        }), 500


@agent_zero_bp.route('/api/user/get-agent-zero-api-key', methods=['POST'])
@require_auth
def retrieve_agent_zero_api_key():
    """
    Retrieve Agent Zero API key and store it for the current user.
    
    Request Body (optional):
        {
            "agent_zero_url": "http://localhost:8080"  // Optional, overrides default
        }
    
    Returns:
        JSON response:
        {
            "success": boolean,
            "message": string,
            "api_key": string (only if success)
        }
    """
    try:
        user = g.user
        db = SupabaseDB.get_instance()
        
        # Get request data
        request_data = request.get_json() or {}
        # Frontend-provided URL is ignored - always use configured URL for connections
        # Always use configured URL for actual connections (ensures correct Docker service name)
        agent_zero_url = Config.AGENT_ZERO_URL
        
        # Check if user already has API key stored
        user_record = db.get_user_by_id(user['id'])
        
        if user_record and user_record.get('agent_zero_api_key'):
            logger.info(f"User {user['id']} already has API key stored")
            return jsonify({
                "success": True,
                "message": "API key already exists",
                "api_key": user_record['agent_zero_api_key']
            }), 200
        
        # Check if user has stored credentials
        credentials = db.get_agent_zero_credentials(user['id'])
        
        # Retrieve API key from Agent Zero (always use configured URL)
        logger.info(f"Retrieving API key from Agent Zero at {agent_zero_url} for user {user['id']}")
        timeout = Config.AGENT_ZERO_REQUEST_TIMEOUT
        
        try:
            # Try to use stored credentials if available
            if credentials:
                logger.info(f"Using stored credentials for user {user['id']}")
                auth_result = authenticate_with_credentials(
                    agent_zero_url=agent_zero_url,
                    username=credentials['username'],
                    password=credentials['password'],
                    timeout=timeout
                )
                api_key = get_api_key_from_agent_zero(
                    agent_zero_url=agent_zero_url,
                    timeout=timeout,
                    session_cookies=auth_result['session_cookies'],
                    csrf_token=auth_result['csrf_token']
                )
            else:
                # Try without authentication (for Agent Zero instances without auth)
                api_key = get_api_key_from_agent_zero(agent_zero_url, timeout=timeout)
        except AgentZeroConnectionError as e:
            logger.error(f"Connection error for user {user['id']} at {agent_zero_url}: {e}")
            error_msg = f"Unable to connect to Agent Zero at {agent_zero_url}. Please ensure it's running and the AGENT_ZERO_URL environment variable is correctly configured."
            if Config.DEBUG:
                error_msg += f" Error: {str(e)}"
            return jsonify({
                "success": False,
                "message": error_msg
            }), 503
        except AgentZeroAuthenticationError as e:
            logger.error(f"Authentication error for user {user['id']} at {agent_zero_url}: {e}")
            # If authentication failed and no credentials stored, suggest connecting
            if not credentials:
                return jsonify({
                    "success": False,
                    "message": "Agent Zero requires authentication. Please use /api/user/connect-agent-zero to provide credentials."
                }), 401
            return jsonify({
                "success": False,
                "message": str(e)
            }), 401
        except AgentZeroAPIKeyNotFoundError as e:
            logger.error(f"API key not found for user {user['id']} at {agent_zero_url}: {e}")
            return jsonify({
                "success": False,
                "message": "API key not found in Agent Zero settings."
            }), 404
        except AgentZeroClientError as e:
            logger.error(f"Client error for user {user['id']} at {agent_zero_url}: {e}")
            error_msg = f"Error retrieving API key: {str(e)}"
            if Config.DEBUG:
                error_msg += f" (URL: {agent_zero_url})"
            return jsonify({
                "success": False,
                "message": error_msg
            }), 500
        
        # Store API key in Supabase (use configured URL for storage)
        try:
            db.update_user_agent_zero_config(
                user_id=user['id'],
                api_key=api_key,
                agent_zero_url=agent_zero_url  # Store configured URL
            )
            
            logger.info(f"API key retrieved and stored successfully for user {user['id']}")
            
            return jsonify({
                "success": True,
                "message": "API key retrieved and stored successfully",
                "api_key": api_key
            }), 200
            
        except Exception as e:
            logger.error(f"Database error storing API key for user {user['id']}: {e}", exc_info=True)
            return jsonify({
                "success": False,
                "message": "Failed to store API key."
            }), 500
        
    except Exception as e:
        logger.error(f"Unexpected error retrieving API key: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "message": "An unexpected error occurred"
        }), 500
