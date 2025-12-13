"""
Agent Zero API Client Service

This module provides functions to interact with Agent Zero backend API,
specifically for retrieving the API key (MCP Server Token) from Agent Zero settings.
"""

import logging
import requests
from typing import Optional, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class AgentZeroClientError(Exception):
    """Base exception for Agent Zero client errors"""
    pass


class AgentZeroConnectionError(AgentZeroClientError):
    """Raised when unable to connect to Agent Zero"""
    pass


class AgentZeroAuthenticationError(AgentZeroClientError):
    """Raised when Agent Zero requires authentication"""
    pass


class AgentZeroAPIKeyNotFoundError(AgentZeroClientError):
    """Raised when API key is not found in Agent Zero settings"""
    pass


def get_csrf_token(agent_zero_url: str, timeout: int = 10) -> str:
    """
    Fetch CSRF token from Agent Zero.
    
    Args:
        agent_zero_url: Base URL of Agent Zero backend (e.g., 'http://localhost:8080')
        timeout: Request timeout in seconds
        
    Returns:
        CSRF token string
        
    Raises:
        AgentZeroConnectionError: If unable to connect to Agent Zero
        AgentZeroAuthenticationError: If Agent Zero requires authentication
    """
    try:
        url = f"{agent_zero_url.rstrip('/')}/csrf_token"
        logger.debug(f"Fetching CSRF token from {url}")
        
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        
        data = response.json()
        token = data.get('token')
        
        if not token:
            raise AgentZeroClientError("CSRF token not found in response")
        
        logger.debug("CSRF token retrieved successfully")
        return token
        
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error to Agent Zero: {e}")
        raise AgentZeroConnectionError(f"Unable to connect to Agent Zero at {agent_zero_url}") from e
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout connecting to Agent Zero: {e}")
        raise AgentZeroConnectionError(f"Timeout connecting to Agent Zero at {agent_zero_url}") from e
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            logger.error("Agent Zero requires authentication")
            raise AgentZeroAuthenticationError("Agent Zero requires authentication. Please configure it without auth or contact support.") from e
        logger.error(f"HTTP error from Agent Zero: {e}")
        raise AgentZeroClientError(f"HTTP error from Agent Zero: {e}") from e
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error to Agent Zero: {e}")
        raise AgentZeroConnectionError(f"Network error connecting to Agent Zero: {e}") from e
    except (KeyError, ValueError) as e:
        logger.error(f"Invalid response format from Agent Zero: {e}")
        raise AgentZeroClientError(f"Invalid response format from Agent Zero: {e}") from e


def login_to_agent_zero(
    agent_zero_url: str,
    username: str,
    password: str,
    timeout: int = 10
) -> Dict[str, str]:
    """
    Login to Agent Zero using username and password.
    
    Args:
        agent_zero_url: Base URL of Agent Zero backend
        username: Username for authentication
        password: Password for authentication
        timeout: Request timeout in seconds
        
    Returns:
        Dictionary of session cookies for subsequent requests
        
    Raises:
        AgentZeroConnectionError: If unable to connect to Agent Zero
        AgentZeroAuthenticationError: If credentials are invalid
    """
    try:
        url = f"{agent_zero_url.rstrip('/')}/login"
        logger.debug(f"Logging in to Agent Zero at {url}")
        
        # Login using form data (username and password fields)
        response = requests.post(
            url,
            data={
                'username': username,
                'password': password
            },
            timeout=timeout,
            allow_redirects=False  # Don't follow redirects, we just need the session cookie
        )
        
        # Check if login was successful
        # Agent Zero redirects to "/" on successful login (302)
        # Returns error on failed login (200 with error message)
        if response.status_code == 302:
            # Success - extract session cookies
            cookies = dict(response.cookies)
            logger.debug("Login successful, session cookies obtained")
            return cookies
        elif response.status_code == 200:
            # Login failed - likely invalid credentials
            logger.error("Login failed: invalid credentials")
            raise AgentZeroAuthenticationError("Invalid username or password")
        else:
            response.raise_for_status()
            
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error to Agent Zero: {e}")
        raise AgentZeroConnectionError(f"Unable to connect to Agent Zero at {agent_zero_url}") from e
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout connecting to Agent Zero: {e}")
        raise AgentZeroConnectionError(f"Timeout connecting to Agent Zero at {agent_zero_url}") from e
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error from Agent Zero: {e}")
        raise AgentZeroClientError(f"HTTP error from Agent Zero: {e}") from e
    except AgentZeroAuthenticationError:
        raise
    except Exception as e:
        logger.error(f"Error logging in to Agent Zero: {e}")
        raise AgentZeroClientError(f"Error logging in to Agent Zero: {e}") from e


def get_csrf_token_with_session(
    agent_zero_url: str,
    session_cookies: Dict[str, str],
    timeout: int = 10
) -> str:
    """
    Fetch CSRF token from Agent Zero using session cookies.
    
    Args:
        agent_zero_url: Base URL of Agent Zero backend
        session_cookies: Session cookies from login_to_agent_zero()
        timeout: Request timeout in seconds
        
    Returns:
        CSRF token string
        
    Raises:
        AgentZeroConnectionError: If unable to connect to Agent Zero
        AgentZeroAuthenticationError: If session is invalid
    """
    try:
        url = f"{agent_zero_url.rstrip('/')}/csrf_token"
        logger.debug(f"Fetching CSRF token with session from {url}")
        
        response = requests.get(url, cookies=session_cookies, timeout=timeout)
        response.raise_for_status()
        
        data = response.json()
        token = data.get('token')
        
        if not token:
            raise AgentZeroClientError("CSRF token not found in response")
        
        logger.debug("CSRF token retrieved successfully with session")
        return token
        
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error to Agent Zero: {e}")
        raise AgentZeroConnectionError(f"Unable to connect to Agent Zero at {agent_zero_url}") from e
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout connecting to Agent Zero: {e}")
        raise AgentZeroConnectionError(f"Timeout connecting to Agent Zero at {agent_zero_url}") from e
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            logger.error("Session invalid or expired")
            raise AgentZeroAuthenticationError("Session invalid or expired. Please re-authenticate.") from e
        logger.error(f"HTTP error from Agent Zero: {e}")
        raise AgentZeroClientError(f"HTTP error from Agent Zero: {e}") from e
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error to Agent Zero: {e}")
        raise AgentZeroConnectionError(f"Network error connecting to Agent Zero: {e}") from e
    except (KeyError, ValueError) as e:
        logger.error(f"Invalid response format from Agent Zero: {e}")
        raise AgentZeroClientError(f"Invalid response format from Agent Zero: {e}") from e


def get_settings(agent_zero_url: str, csrf_token: Optional[str] = None, timeout: int = 10, session_cookies: Optional[Dict[str, str]] = None, api_key: Optional[str] = None) -> dict:
    """
    Call Agent Zero /api/settings_get endpoint to retrieve settings.
    
    Args:
        agent_zero_url: Base URL of Agent Zero backend
        csrf_token: CSRF token obtained from get_csrf_token() or get_csrf_token_with_session() (optional if api_key provided)
        timeout: Request timeout in seconds
        session_cookies: Optional session cookies for authenticated requests
        api_key: Optional API key for authentication (alternative to csrf_token)
        
    Returns:
        Settings data dictionary
        
    Raises:
        AgentZeroConnectionError: If unable to connect to Agent Zero
        AgentZeroAuthenticationError: If Agent Zero requires authentication
    """
    try:
        url = f"{agent_zero_url.rstrip('/')}/api/settings_get"
        logger.debug(f"Fetching settings from {url}")
        
        headers = {
            'Content-Type': 'application/json',
        }
        
        # Use API key if provided, otherwise use CSRF token
        if api_key:
            headers['X-API-KEY'] = api_key
        elif csrf_token:
            headers['X-CSRF-Token'] = csrf_token
        else:
            raise AgentZeroAuthenticationError("Either csrf_token or api_key must be provided")
        
        response = requests.post(
            url,
            json={},
            headers=headers,
            cookies=session_cookies if session_cookies else None,
            timeout=timeout
        )
        response.raise_for_status()
        
        data = response.json()
        logger.debug("Settings retrieved successfully")
        return data
        
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error to Agent Zero: {e}")
        raise AgentZeroConnectionError(f"Unable to connect to Agent Zero at {agent_zero_url}") from e
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout connecting to Agent Zero: {e}")
        raise AgentZeroConnectionError(f"Timeout connecting to Agent Zero at {agent_zero_url}") from e
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            logger.error("Agent Zero requires authentication")
            raise AgentZeroAuthenticationError("Agent Zero requires authentication. Please configure it without auth or contact support.") from e
        if e.response.status_code == 403:
            logger.error("CSRF token invalid or missing")
            raise AgentZeroAuthenticationError("CSRF token invalid or missing") from e
        logger.error(f"HTTP error from Agent Zero: {e}")
        raise AgentZeroClientError(f"HTTP error from Agent Zero: {e}") from e
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error to Agent Zero: {e}")
        raise AgentZeroConnectionError(f"Network error connecting to Agent Zero: {e}") from e
    except (KeyError, ValueError) as e:
        logger.error(f"Invalid response format from Agent Zero: {e}")
        raise AgentZeroClientError(f"Invalid response format from Agent Zero: {e}") from e


def extract_api_key(settings_data: dict) -> str:
    """
    Extract MCP Server Token (API key) from Agent Zero settings response.
    
    Args:
        settings_data: Settings data dictionary from get_settings()
        
    Returns:
        API key string
        
    Raises:
        AgentZeroAPIKeyNotFoundError: If API key not found in settings
    """
    try:
        settings = settings_data.get('settings', {})
        sections = settings.get('sections', [])
        
        # Find the MCP section
        mcp_section = None
        for section in sections:
            if section.get('id') == 'mcp':
                mcp_section = section
                break
        
        if not mcp_section:
            logger.error("MCP section not found in settings")
            raise AgentZeroAPIKeyNotFoundError("MCP section not found in Agent Zero settings")
        
        # Find the mcp_server_token field
        fields = mcp_section.get('fields', [])
        token_field = None
        for field in fields:
            if field.get('id') == 'mcp_server_token':
                token_field = field
                break
        
        if not token_field:
            logger.error("mcp_server_token field not found in MCP section")
            raise AgentZeroAPIKeyNotFoundError("API key field not found in Agent Zero settings")
        
        api_key = token_field.get('value')
        if not api_key:
            logger.error("API key value is empty")
            raise AgentZeroAPIKeyNotFoundError("API key not found in Agent Zero settings")
        
        logger.debug("API key extracted successfully")
        return api_key
        
    except (KeyError, TypeError) as e:
        logger.error(f"Error extracting API key: {e}")
        raise AgentZeroAPIKeyNotFoundError(f"Error extracting API key from settings: {e}") from e


def authenticate_with_credentials(
    agent_zero_url: str,
    username: str,
    password: str,
    timeout: int = 10
) -> Dict[str, any]:
    """
    Authenticate with Agent Zero using username/password and get session + CSRF token.
    
    Args:
        agent_zero_url: Base URL of Agent Zero backend
        username: Username for authentication
        password: Password for authentication
        timeout: Request timeout in seconds
        
    Returns:
        Dictionary with 'session_cookies' and 'csrf_token' keys
        
    Raises:
        AgentZeroConnectionError: If unable to connect to Agent Zero
        AgentZeroAuthenticationError: If credentials are invalid
    """
    logger.info(f"Authenticating with Agent Zero at {agent_zero_url}")
    
    try:
        # Step 1: Login to get session cookies
        session_cookies = login_to_agent_zero(agent_zero_url, username, password, timeout)
        
        # Step 2: Get CSRF token using session
        csrf_token = get_csrf_token_with_session(agent_zero_url, session_cookies, timeout)
        
        logger.info("Authentication successful")
        return {
            'session_cookies': session_cookies,
            'csrf_token': csrf_token
        }
        
    except (AgentZeroConnectionError, AgentZeroAuthenticationError):
        # Re-raise our custom exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error during authentication: {e}")
        raise AgentZeroClientError(f"Unexpected error during authentication: {e}") from e


def _determine_field_section(field_id: str) -> str:
    """
    Determine which section a field belongs to based on its ID.
    
    Args:
        field_id: The field ID (e.g., 'api_key_openai', 'chat_model_name')
        
    Returns:
        Section ID (e.g., 'api_keys', 'chat_model')
    """
    # API keys go to api_keys section
    if field_id.startswith('api_key_'):
        return 'api_keys'
    
    # Model fields
    if field_id.startswith('chat_model_'):
        return 'chat_model'
    if field_id.startswith('util_model_'):
        return 'util_model'
    if field_id.startswith('embed_model_'):
        return 'embed_model'
    if field_id.startswith('browser_model_'):
        return 'browser_model'
    
    # LiteLLM fields
    if field_id.startswith('litellm_') or field_id.endswith('_kwargs'):
        if 'litellm' in field_id.lower():
            return 'litellm'
        # Other _kwargs fields might be in different sections, default to agent
        return 'agent'
    
    # Memory fields
    if field_id.startswith('memory_'):
        return 'memory'
    
    # Speech fields
    if field_id.startswith('speech_'):
        return 'speech'
    
    # MCP fields
    if field_id.startswith('mcp_'):
        return 'mcp'
    
    # A2A fields
    if field_id.startswith('a2a_'):
        return 'a2a'
    
    # Auth fields
    if field_id.startswith('auth_'):
        return 'auth'
    
    # Default to agent section for unknown fields
    return 'agent'


def _transform_settings_to_sections_format(flat_settings: dict) -> dict:
    """
    Transform a flat dictionary of settings to the sections/fields format required by Agent Zero.
    
    Args:
        flat_settings: Dictionary with field_id: value pairs (e.g., {'api_key_openai': 'sk-...'})
        
    Returns:
        Dictionary in sections format:
        {
            'sections': [
                {'id': 'api_keys', 'fields': [{'id': 'api_key_openai', 'value': 'sk-...'}]},
                ...
            ]
        }
    """
    # Group fields by section
    sections_dict = {}
    
    for field_id, value in flat_settings.items():
        section_id = _determine_field_section(field_id)
        
        if section_id not in sections_dict:
            sections_dict[section_id] = []
        
        sections_dict[section_id].append({
            'id': field_id,
            'value': value
        })
    
    # Convert to sections array format
    sections = [
        {
            'id': section_id,
            'fields': fields
        }
        for section_id, fields in sections_dict.items()
    ]
    
    return {'sections': sections}


def set_settings(
    agent_zero_url: str,
    api_key: str,
    settings_data: dict,
    timeout: int = 10
) -> dict:
    """
    Update Agent Zero settings using API key authentication.
    
    This function accepts settings in two formats:
    1. Flat dictionary: {'api_key_openai': 'sk-...', 'chat_model_name': 'gpt-4'}
       - Will be transformed to sections format
       - Only fields included in the dictionary will be updated
       - Agent Zero preserves unchanged fields automatically
       - To preserve existing values, frontend should send '************' placeholder
    2. Sections format: {'sections': [{'id': 'api_keys', 'fields': [...]}]}
       - Used as-is (backward compatible)
    
    Args:
        agent_zero_url: Base URL of Agent Zero backend
        api_key: Agent Zero API key (MCP Server Token)
        settings_data: Settings dictionary to update. Can be:
            - Flat dictionary (field_id: value pairs) - will be transformed to sections format
            - Sections format ({'sections': [...]}) - used as-is
        timeout: Request timeout in seconds
        
    Returns:
        Response data dictionary from Agent Zero
        
    Raises:
        AgentZeroConnectionError: If unable to connect to Agent Zero
        AgentZeroAuthenticationError: If API key is invalid
        AgentZeroClientError: For other client errors
    """
    try:
        # Check if settings_data is already in sections format
        if 'sections' in settings_data and isinstance(settings_data.get('sections'), list):
            # Already in sections format - use as-is
            logger.debug("Settings data already in sections format, using as-is")
            transformed_settings = settings_data
        else:
            # Flat dictionary format - transform to sections format
            # Agent Zero's convert_in() only processes fields that are sent, so partial updates are safe
            logger.debug("Settings data is flat dictionary, transforming to sections format")
            transformed_settings = _transform_settings_to_sections_format(settings_data)
        
        url = f"{agent_zero_url.rstrip('/')}/api/settings_set"
        logger.debug(f"Updating settings at {url}")
        
        headers = {
            'Content-Type': 'application/json',
            'X-API-KEY': api_key
        }
        
        response = requests.post(
            url,
            json=transformed_settings,
            headers=headers,
            timeout=timeout
        )
        
        response.raise_for_status()
        
        data = response.json()
        logger.debug("Settings updated successfully")
        return data
        
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error to Agent Zero: {e}")
        raise AgentZeroConnectionError(f"Unable to connect to Agent Zero at {agent_zero_url}") from e
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout connecting to Agent Zero: {e}")
        raise AgentZeroConnectionError(f"Timeout connecting to Agent Zero at {agent_zero_url}") from e
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            logger.error("API key invalid")
            raise AgentZeroAuthenticationError("Invalid API key") from e
        logger.error(f"HTTP error from Agent Zero: {e}")
        raise AgentZeroClientError(f"HTTP error from Agent Zero: {e}") from e
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error to Agent Zero: {e}")
        raise AgentZeroConnectionError(f"Network error connecting to Agent Zero: {e}") from e
    except (KeyError, ValueError) as e:
        logger.error(f"Invalid response format from Agent Zero: {e}")
        raise AgentZeroClientError(f"Invalid response format from Agent Zero: {e}") from e


def get_api_key_from_agent_zero(agent_zero_url: str, timeout: int = 10, session_cookies: Optional[Dict[str, str]] = None, csrf_token: Optional[str] = None) -> str:
    """
    Main function that orchestrates the API key retrieval from Agent Zero.
    
    This function:
    1. Gets CSRF token from Agent Zero (with optional session)
    2. Retrieves settings using the CSRF token
    3. Extracts the MCP Server Token (API key) from settings
    
    Args:
        agent_zero_url: Base URL of Agent Zero backend (e.g., 'http://localhost:8080')
        timeout: Request timeout in seconds
        session_cookies: Optional session cookies for authenticated requests
        csrf_token: Optional CSRF token (if already obtained, otherwise will be fetched)
        
    Returns:
        API key string (MCP Server Token)
        
    Raises:
        AgentZeroConnectionError: If unable to connect to Agent Zero
        AgentZeroAuthenticationError: If Agent Zero requires authentication
        AgentZeroAPIKeyNotFoundError: If API key not found in settings
    """
    logger.info(f"Retrieving API key from Agent Zero at {agent_zero_url}")
    
    try:
        # Step 1: Get CSRF token (if not provided)
        if not csrf_token:
            if session_cookies:
                csrf_token = get_csrf_token_with_session(agent_zero_url, session_cookies, timeout)
            else:
                csrf_token = get_csrf_token(agent_zero_url, timeout)
        
        # Step 2: Get settings
        settings_data = get_settings(agent_zero_url, csrf_token, timeout, session_cookies)
        
        # Step 3: Extract API key
        api_key = extract_api_key(settings_data)
        
        logger.info("API key retrieved successfully from Agent Zero")
        return api_key
        
    except (AgentZeroConnectionError, AgentZeroAuthenticationError, AgentZeroAPIKeyNotFoundError):
        # Re-raise our custom exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error retrieving API key: {e}")
        raise AgentZeroClientError(f"Unexpected error retrieving API key: {e}") from e
