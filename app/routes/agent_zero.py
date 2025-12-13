"""
Agent Zero Integration Routes

Flask routes for managing Agent Zero API key retrieval and status.
"""

import logging
from flask import Blueprint, request, jsonify, g

from app.services.agent_zero_client import (
    get_api_key_from_agent_zero,
    authenticate_with_credentials,
    set_settings,
    AgentZeroConnectionError,
    AgentZeroAuthenticationError,
    AgentZeroAPIKeyNotFoundError,
    AgentZeroClientError
)
from app.database import SupabaseDB
from app.auth import require_auth
from app.config import Config

logger = logging.getLogger(__name__)

# Create blueprint
agent_zero_bp = Blueprint('agent_zero', __name__)


@agent_zero_bp.route('/api/user/agent-zero-status', methods=['GET'])
@require_auth
def get_agent_zero_status():
    """
    Get Agent Zero API key status for the current user.
    
    Returns:
        JSON response with status information:
        {
            "has_api_key": boolean,
            "agent_zero_url": string,
            "api_key_retrieved_at": timestamp or null
        }
    """
    try:
        user = g.user
        db = SupabaseDB.get_instance()
        
        # Get user's Agent Zero status from Supabase
        status = db.get_user_agent_zero_status(user['id'])
        
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
    try:
        user = g.user
        db = SupabaseDB.get_instance()
        
        # Get request data
        request_data = request.get_json() or {}
        agent_zero_url = request_data.get('agent_zero_url') or Config.AGENT_ZERO_URL
        username = request_data.get('username')
        password = request_data.get('password')
        
        # Validate input
        if not username or not password:
            return jsonify({
                "success": False,
                "message": "Username and password are required"
            }), 400
        
        if not agent_zero_url.startswith(('http://', 'https://')):
            return jsonify({
                "success": False,
                "message": "Invalid Agent Zero URL"
            }), 400
        
        timeout = Config.AGENT_ZERO_REQUEST_TIMEOUT
        
        # Store credentials in database
        try:
            db.store_agent_zero_credentials(
                user_id=user['id'],
                username=username,
                password=password,
                agent_zero_url=agent_zero_url
            )
            logger.info(f"Stored credentials for user {user['id']}")
        except Exception as e:
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
        try:
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
            logger.error(f"Connection error for user {user['id']}: {e}")
            return jsonify({
                "success": False,
                "message": "Unable to connect to Agent Zero. Please ensure it's running."
            }), 503
        except AgentZeroAuthenticationError as e:
            logger.error(f"Authentication error for user {user['id']}: {e}")
            return jsonify({
                "success": False,
                "message": f"Authentication failed: {str(e)}"
            }), 401
        except AgentZeroAPIKeyNotFoundError as e:
            logger.error(f"API key not found for user {user['id']}: {e}")
            return jsonify({
                "success": False,
                "message": "API key not found in Agent Zero settings."
            }), 404
        except AgentZeroClientError as e:
            logger.error(f"Client error for user {user['id']}: {e}")
            return jsonify({
                "success": False,
                "message": f"Error retrieving API key: {str(e)}"
            }), 500
        
        # Store API key in database
        try:
            db.update_user_agent_zero_config(
                user_id=user['id'],
                api_key=api_key,
                agent_zero_url=agent_zero_url
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
        agent_zero_url = user_record.get('agent_zero_url') or Config.AGENT_ZERO_URL
        
        timeout = Config.AGENT_ZERO_REQUEST_TIMEOUT
        
        # Update settings in Agent Zero
        try:
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
            logger.error(f"Connection error for user {user['id']}: {e}")
            return jsonify({
                "success": False,
                "message": "Unable to connect to Agent Zero. Please ensure it's running."
            }), 503
        except AgentZeroAuthenticationError as e:
            logger.error(f"Authentication error for user {user['id']}: {e}")
            return jsonify({
                "success": False,
                "message": f"Authentication failed: {str(e)}. Please reconnect to Agent Zero."
            }), 401
        except AgentZeroClientError as e:
            logger.error(f"Client error for user {user['id']}: {e}")
            return jsonify({
                "success": False,
                "message": f"Error updating settings: {str(e)}"
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
        
        # Get Agent Zero URL from request or use default
        request_data = request.get_json() or {}
        agent_zero_url = request_data.get('agent_zero_url') or Config.AGENT_ZERO_URL
        
        # Validate URL to prevent SSRF attacks
        if not agent_zero_url.startswith(('http://', 'https://')):
            return jsonify({
                "success": False,
                "message": "Invalid Agent Zero URL"
            }), 400
        
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
        
        # Retrieve API key from Agent Zero
        logger.info(f"Retrieving API key from Agent Zero for user {user['id']}")
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
            logger.error(f"Connection error for user {user['id']}: {e}")
            return jsonify({
                "success": False,
                "message": "Unable to connect to Agent Zero. Please ensure it's running."
            }), 503
        except AgentZeroAuthenticationError as e:
            logger.error(f"Authentication error for user {user['id']}: {e}")
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
            logger.error(f"API key not found for user {user['id']}: {e}")
            return jsonify({
                "success": False,
                "message": "API key not found in Agent Zero settings."
            }), 404
        except AgentZeroClientError as e:
            logger.error(f"Client error for user {user['id']}: {e}")
            return jsonify({
                "success": False,
                "message": f"Error retrieving API key: {str(e)}"
            }), 500
        
        # Store API key in Supabase
        try:
            db.update_user_agent_zero_config(
                user_id=user['id'],
                api_key=api_key,
                agent_zero_url=agent_zero_url
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
