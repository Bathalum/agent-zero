"""
Supabase Database Client

Production-ready Supabase integration for user management.
"""

import os
import logging
import json
from typing import Optional, Dict, Any
from datetime import datetime
from supabase import create_client, Client

from app.utils.encryption import encrypt_password, decrypt_password

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


class SupabaseDB:
    """Supabase database client wrapper."""
    
    _instance: Optional['SupabaseDB'] = None
    _client: Optional[Client] = None
    
    def __init__(self):
        # #region agent log
        _debug_log("app/database.py:__init__", "SupabaseDB initialization started", {}, "C")
        # #endregion
        
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')  # Use service role for backend operations
        
        # #region agent log
        _debug_log("app/database.py:__init__", "Environment variables checked", {
            "has_url": bool(supabase_url),
            "has_key": bool(supabase_key),
            "url_length": len(supabase_url) if supabase_url else 0,
            "key_length": len(supabase_key) if supabase_key else 0
        }, "C")
        # #endregion
        
        if not supabase_url or not supabase_key:
            # #region agent log
            _debug_log("app/database.py:__init__", "Missing environment variables", {
                "missing_url": not supabase_url,
                "missing_key": not supabase_key
            }, "C")
            # #endregion
            raise ValueError(
                "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables are required"
            )
        
        # For backend usage, we don't need ClientOptions - just create client directly
        # ClientOptions with storage attribute causes compatibility issues with some versions
        try:
            # #region agent log
            _debug_log("app/database.py:__init__", "Creating Supabase client", {"url": supabase_url[:50] + "..." if supabase_url else None}, "A")
            # #endregion
            self._client = create_client(supabase_url, supabase_key)
            # #region agent log
            _debug_log("app/database.py:__init__", "Supabase client created successfully", {"client_exists": self._client is not None}, "A")
            # #endregion
            logger.info("Supabase client initialized")
        except AttributeError as e:
            # Handle ClientOptions storage attribute error (supabase-py version compatibility issue)
            # #region agent log
            _debug_log("app/database.py:__init__", "AttributeError caught during client creation", {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "error_str": str(e),
                "contains_storage": 'storage' in str(e),
                "contains_clientoptions": 'ClientOptions' in str(e),
                "traceback_available": hasattr(e, '__traceback__')
            }, "A")
            # #endregion
            if 'storage' in str(e) and 'ClientOptions' in str(e):
                # #region agent log
                _debug_log("app/database.py:__init__", "Supabase client creation failed - ClientOptions storage error", {
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "suggestion": "Try updating supabase-py: pip install --upgrade supabase"
                }, "A")
                # #endregion
                raise RuntimeError(
                    f"Supabase client initialization failed due to version compatibility issue: {str(e)}. "
                    "Try updating supabase-py: pip install --upgrade supabase"
                ) from e
            # #region agent log
            _debug_log("app/database.py:__init__", "AttributeError not matching ClientOptions pattern, re-raising", {
                "error_message": str(e)
            }, "A")
            # #endregion
            raise
        except Exception as e:
            # #region agent log
            _debug_log("app/database.py:__init__", "Supabase client creation failed", {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "error_str": str(e)
            }, "A")
            # #endregion
            raise
    
    @classmethod
    def get_instance(cls) -> 'SupabaseDB':
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @property
    def client(self) -> Client:
        """Get Supabase client."""
        if self._client is None:
            raise RuntimeError("Supabase client not initialized")
        return self._client
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user by ID from Supabase.
        
        Args:
            user_id: User UUID
            
        Returns:
            User record or None
        """
        try:
            response = self.client.table('account_users').select('*').eq('id', user_id).execute()
            
            if response.data:
                return response.data[0]
            
            return None
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}", exc_info=True)
            raise
    
    def ensure_user_exists(self, user_id: str, email: Optional[str] = None) -> Dict[str, Any]:
        """
        Ensure user exists in account_users table. Creates record if it doesn't exist.
        
        This method solves the chicken-egg problem where authenticated users from auth.users
        don't have a corresponding record in account_users until they connect to Agent Zero.
        
        Args:
            user_id: User UUID from auth.users
            email: User email (optional, for initial record creation)
            
        Returns:
            User record (existing or newly created)
        """
        try:
            # Check if user already exists
            user = self.get_user_by_id(user_id)
            if user:
                return user
            
            # User doesn't exist - create minimal record
            create_data = {
                'id': user_id
            }
            
            # Add email if provided (useful for initial setup)
            if email:
                create_data['email'] = email
            
            try:
                response = self.client.table('account_users').insert(create_data).execute()
                if response.data:
                    logger.info(f"Created new user profile for user {user_id}")
                    return response.data[0]
                else:
                    # If insert succeeded but no data returned, fetch the user
                    created_user = self.get_user_by_id(user_id)
                    if created_user:
                        logger.info(f"Created new user profile for user {user_id}")
                        return created_user
                    raise ValueError(f"Failed to create user profile for {user_id}")
            except Exception as create_error:
                logger.error(f"Error creating user profile for {user_id}: {create_error}", exc_info=True)
                raise ValueError(f"Failed to create user profile: {str(create_error)}") from create_error
                
        except Exception as e:
            logger.error(f"Error ensuring user exists for {user_id}: {e}", exc_info=True)
            raise
    
    def store_agent_zero_credentials(
        self,
        user_id: str,
        username: str,
        password: str,
        agent_zero_url: str,
        email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Store Agent Zero credentials for a user.
        
        Encrypts password before storing.
        
        Args:
            user_id: User UUID
            username: Agent Zero username
            password: Agent Zero password (will be encrypted)
            agent_zero_url: Agent Zero instance URL
            email: Optional email for user creation (if user doesn't exist)
            
        Returns:
            Updated user record
        """
        # #region agent log
        _debug_log("app/database.py:store_agent_zero_credentials", "Function entry", {
            "user_id": user_id,
            "username": username,
            "has_password": bool(password),
            "agent_zero_url": agent_zero_url,
            "has_email_param": email is not None,
            "email_param": email
        }, "B")
        # #endregion
        
        try:
            # #region agent log
            _debug_log("app/database.py:store_agent_zero_credentials", "Encrypting password", {}, "E")
            # #endregion
            encrypted_password = encrypt_password(password)
            
            update_data = {
                'agent_zero_username': username,
                'agent_zero_password_encrypted': encrypted_password,
                'agent_zero_url': agent_zero_url,
            }
            
            # #region agent log
            _debug_log("app/database.py:store_agent_zero_credentials", "Checking if user exists", {"user_id": user_id}, "E")
            # #endregion
            
            # Check if user exists, create if not
            user = self.get_user_by_id(user_id)
            
            # #region agent log
            _debug_log("app/database.py:store_agent_zero_credentials", "User lookup result", {
                "user_exists": user is not None,
                "user_id": user_id
            }, "E")
            # #endregion
            
            if not user:
                # User doesn't exist in account_users - create them
                # Create user record with credentials
                create_data = {
                    'id': user_id,
                    **update_data
                }
                # Add email if provided (required for non-null constraint)
                if email:
                    create_data['email'] = email
                # #region agent log
                _debug_log("app/database.py:store_agent_zero_credentials", "create_data before insert", {
                    "user_id": user_id,
                    "create_data_keys": list(create_data.keys()),
                    "has_email": 'email' in create_data,
                    "email_value": create_data.get('email'),
                    "has_id": 'id' in create_data,
                    "create_data_values": {k: (v[:20] + "..." if isinstance(v, str) and len(v) > 20 else v) for k, v in create_data.items() if k != 'agent_zero_password_encrypted'}
                }, "B")
                # #endregion
                try:
                    # #region agent log
                    _debug_log("app/database.py:store_agent_zero_credentials", "Inserting new user", {
                        "user_id": user_id,
                        "has_username": 'agent_zero_username' in create_data,
                        "has_encrypted_password": 'agent_zero_password_encrypted' in create_data
                    }, "E")
                    # #endregion
                    # Insert returns data by default in Supabase Python client
                    response = self.client.table('account_users').insert(create_data).execute()
                    # #region agent log
                    _debug_log("app/database.py:store_agent_zero_credentials", "Insert response received", {
                        "has_data": bool(response.data),
                        "data_count": len(response.data) if response.data else 0
                    }, "E")
                    # #endregion
                    if response.data:
                        logger.info(f"Created new user record and stored Agent Zero credentials for user {user_id}")
                        return response.data[0]
                    else:
                        # If insert succeeded but no data returned, fetch the user
                        created_user = self.get_user_by_id(user_id)
                        if created_user:
                            logger.info(f"Created new user record and stored Agent Zero credentials for user {user_id}")
                            return created_user
                        raise ValueError(f"Failed to create user {user_id}")
                except Exception as create_error:
                    # #region agent log
                    _debug_log("app/database.py:store_agent_zero_credentials", "Insert failed", {
                        "error_type": type(create_error).__name__,
                        "error_message": str(create_error),
                        "error_str_lower": str(create_error).lower()
                    }, "D")
                    # #endregion
                    logger.error(f"Error creating user {user_id}: {create_error}", exc_info=True)
                    raise ValueError(f"Failed to create user record: {str(create_error)}") from create_error
            
            # User exists - update their credentials
            try:
                # #region agent log
                _debug_log("app/database.py:store_agent_zero_credentials", "Updating existing user", {
                    "user_id": user_id,
                    "update_fields": list(update_data.keys())
                }, "E")
                # #endregion
                # Perform update (some Supabase client versions don't support .select() after .update())
                # We'll fetch the user separately after update to return the updated data
                self.client.table('account_users').update(update_data).eq('id', user_id).execute()
                # #region agent log
                _debug_log("app/database.py:store_agent_zero_credentials", "Update executed successfully", {
                    "user_id": user_id
                }, "E")
                # #endregion
            except Exception as db_error:
                # #region agent log
                error_str = str(db_error)
                _debug_log("app/database.py:store_agent_zero_credentials", "Update failed", {
                    "error_type": type(db_error).__name__,
                    "error_message": error_str,
                    "error_str_lower": error_str.lower(),
                    "contains_password_encrypted": 'agent_zero_password_encrypted' in error_str,
                    "contains_pgrst204": 'PGRST204' in error_str
                }, "D")
                # #endregion
                # Check if it's a missing column error
                if 'agent_zero_password_encrypted' in error_str or 'PGRST204' in error_str:
                    raise ValueError(
                        "Database migration required: The 'agent_zero_password_encrypted' column is missing. "
                        "Please run the migration in migrations/add_agent_zero_credentials.sql in your Supabase SQL Editor."
                    ) from db_error
                raise
            
            # Fetch the updated user to return
            updated_user = self.get_user_by_id(user_id)
            if not updated_user:
                raise ValueError(f"User {user_id} not found after update")
            
            logger.info(f"Stored Agent Zero credentials for user {user_id}")
            
            # #region agent log
            _debug_log("app/database.py:store_agent_zero_credentials", "Function exit success", {
                "user_id": user_id,
                "returned_data": bool(updated_user)
            }, "E")
            # #endregion
            
            return updated_user
            
        except Exception as e:
            # #region agent log
            _debug_log("app/database.py:store_agent_zero_credentials", "Function exit error", {
                "user_id": user_id,
                "error_type": type(e).__name__,
                "error_message": str(e)
            }, "E")
            # #endregion
            logger.error(f"Error storing Agent Zero credentials for user {user_id}: {e}", exc_info=True)
            raise
    
    def get_agent_zero_credentials(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get Agent Zero credentials for a user.
        
        Decrypts password before returning.
        
        Args:
            user_id: User UUID
            
        Returns:
            Dict with 'username', 'password', 'agent_zero_url' or None if not found
        """
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return None
            
            username = user.get('agent_zero_username')
            encrypted_password = user.get('agent_zero_password_encrypted')
            url = user.get('agent_zero_url')
            
            if not username or not encrypted_password:
                return None
            
            password = decrypt_password(encrypted_password)
            
            return {
                'username': username,
                'password': password,
                'agent_zero_url': url
            }
            
        except Exception as e:
            logger.error(f"Error getting Agent Zero credentials for user {user_id}: {e}", exc_info=True)
            raise
    
    def clear_agent_zero_credentials(self, user_id: str) -> Dict[str, Any]:
        """
        Clear Agent Zero credentials and API key for a user.
        
        Sets the following fields to NULL:
        - agent_zero_username
        - agent_zero_password_encrypted
        - agent_zero_api_key
        - agent_zero_api_key_retrieved_at
        
        Note: agent_zero_url is preserved for reconnection purposes.
        
        Args:
            user_id: User UUID
            
        Returns:
            Updated user record
        """
        try:
            # Update account_users table to clear credentials
            update_data = {
                'agent_zero_username': None,
                'agent_zero_password_encrypted': None,
                'agent_zero_api_key': None,
                'agent_zero_api_key_retrieved_at': None
            }
            
            # Perform update (some Supabase client versions don't support .select() after .update())
            self.client.table('account_users').update(update_data).eq('id', user_id).execute()
            
            # Fetch the updated user to return
            updated_user = self.get_user_by_id(user_id)
            if not updated_user:
                # User not found in account_users table
                logger.warning(f"User {user_id} not found in account_users table when clearing credentials")
                # Return empty dict to indicate user not found
                return {}
            
            logger.info(f"Cleared Agent Zero credentials for user {user_id}")
            return updated_user
            
        except Exception as e:
            logger.error(f"Error clearing Agent Zero credentials for user {user_id}: {e}", exc_info=True)
            raise
    
    def update_user_agent_zero_config(
        self,
        user_id: str,
        api_key: str,
        agent_zero_url: str,
        instance_id: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update user's Agent Zero configuration.
        
        Args:
            user_id: User UUID
            api_key: Agent Zero API key
            agent_zero_url: Agent Zero instance URL
            instance_id: Optional instance ID
            username: Optional username (will encrypt password if provided)
            password: Optional password (requires username, will be encrypted)
            
        Returns:
            Updated user record
        """
        try:
            update_data = {
                'agent_zero_api_key': api_key,
                'agent_zero_url': agent_zero_url,
                'agent_zero_api_key_retrieved_at': datetime.utcnow().isoformat(),
            }
            
            if instance_id:
                update_data['agent_zero_instance_id'] = instance_id
            
            if username and password:
                update_data['agent_zero_username'] = username
                update_data['agent_zero_password_encrypted'] = encrypt_password(password)
            
            # Perform update (some Supabase client versions don't support .select() after .update())
            self.client.table('account_users').update(update_data).eq('id', user_id).execute()
            
            # Fetch the updated user to return
            updated_user = self.get_user_by_id(user_id)
            if not updated_user:
                raise ValueError(f"User {user_id} not found")
            
            logger.info(f"Updated Agent Zero config for user {user_id}")
            return updated_user
            
        except Exception as e:
            logger.error(f"Error updating user {user_id} Agent Zero config: {e}", exc_info=True)
            raise
    
    def get_user_agent_zero_status(self, user_id: str) -> Dict[str, Any]:
        """
        Get user's Agent Zero status.
        
        Args:
            user_id: User UUID
            
        Returns:
            Status dictionary
        """
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return {
                    'has_api_key': False,
                    'agent_zero_url': None,
                    'api_key_retrieved_at': None
                }
            
            return {
                'has_api_key': bool(user.get('agent_zero_api_key')),
                'agent_zero_url': user.get('agent_zero_url'),
                'api_key_retrieved_at': user.get('agent_zero_api_key_retrieved_at')
            }
        except Exception as e:
            logger.error(f"Error getting Agent Zero status for user {user_id}: {e}", exc_info=True)
            raise
