"""
Supabase Database Client

Production-ready Supabase integration for user management.
"""

import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from supabase import create_client, Client

from app.utils.encryption import encrypt_password, decrypt_password

logger = logging.getLogger(__name__)


class SupabaseDB:
    """Supabase database client wrapper."""
    
    _instance: Optional['SupabaseDB'] = None
    _client: Optional[Client] = None
    
    def __init__(self):
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')  # Use service role for backend operations
        
        if not supabase_url or not supabase_key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables are required"
            )
        
        # For backend usage, we don't need ClientOptions - just create client directly
        # ClientOptions with storage attribute causes compatibility issues with some versions
        self._client = create_client(supabase_url, supabase_key)
        logger.info("Supabase client initialized")
    
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
    
    def store_agent_zero_credentials(
        self,
        user_id: str,
        username: str,
        password: str,
        agent_zero_url: str
    ) -> Dict[str, Any]:
        """
        Store Agent Zero credentials for a user.
        
        Encrypts password before storing.
        
        Args:
            user_id: User UUID
            username: Agent Zero username
            password: Agent Zero password (will be encrypted)
            agent_zero_url: Agent Zero instance URL
            
        Returns:
            Updated user record
        """
        try:
            encrypted_password = encrypt_password(password)
            
            update_data = {
                'agent_zero_username': username,
                'agent_zero_password_encrypted': encrypted_password,
                'agent_zero_url': agent_zero_url,
            }
            
            # Check if user exists, create if not
            user = self.get_user_by_id(user_id)
            
            if not user:
                # User doesn't exist in account_users - create them
                # Create user record with credentials
                create_data = {
                    'id': user_id,
                    **update_data
                }
                try:
                    # Insert returns data by default in Supabase Python client
                    response = self.client.table('account_users').insert(create_data).execute()
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
                    logger.error(f"Error creating user {user_id}: {create_error}", exc_info=True)
                    raise ValueError(f"Failed to create user record: {str(create_error)}") from create_error
            
            # User exists - update their credentials
            try:
                # Use .select('*') to ensure we get the updated row back
                response = self.client.table('account_users').update(update_data).eq('id', user_id).select('*').execute()
            except Exception as db_error:
                # Check if it's a missing column error
                error_str = str(db_error)
                if 'agent_zero_password_encrypted' in error_str or 'PGRST204' in error_str:
                    raise ValueError(
                        "Database migration required: The 'agent_zero_password_encrypted' column is missing. "
                        "Please run the migration in migrations/add_agent_zero_credentials.sql in your Supabase SQL Editor."
                    ) from db_error
                raise
            
            if not response.data:
                # Fallback: fetch the user again to verify update succeeded
                updated_user = self.get_user_by_id(user_id)
                if not updated_user:
                    raise ValueError(f"User {user_id} not found after update")
                # Update succeeded but no data returned - use fetched user
                return updated_user
            
            logger.info(f"Stored Agent Zero credentials for user {user_id}")
            
            return response.data[0]
            
        except Exception as e:
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
            
            response = self.client.table('account_users').update(update_data).eq('id', user_id).select('*').execute()
            
            if not response.data:
                # User not found in account_users table
                logger.warning(f"User {user_id} not found in account_users table when clearing credentials")
                # Return empty dict to indicate user not found
                return {}
            
            logger.info(f"Cleared Agent Zero credentials for user {user_id}")
            return response.data[0]
            
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
            
            response = self.client.table('account_users').update(update_data).eq('id', user_id).execute()
            
            if not response.data:
                raise ValueError(f"User {user_id} not found")
            
            logger.info(f"Updated Agent Zero config for user {user_id}")
            return response.data[0]
            
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
