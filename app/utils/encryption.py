"""
Encryption utilities for securely storing passwords.

Uses Fernet symmetric encryption to encrypt/decrypt passwords for Agent Zero authentication.
"""

import os
import base64
import hashlib
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

# Cache the encryption key
_encryption_key = None


def _get_encryption_key() -> bytes:
    """
    Get or generate encryption key from FLASK_SECRET_KEY.
    
    Derives a Fernet key from FLASK_SECRET_KEY using PBKDF2.
    
    Returns:
        Fernet encryption key bytes
    """
    global _encryption_key
    
    if _encryption_key is not None:
        return _encryption_key
    
    secret_key = os.getenv('FLASK_SECRET_KEY')
    if not secret_key:
        raise ValueError(
            "FLASK_SECRET_KEY environment variable is required for password encryption"
        )
    
    # Use a salt based on the secret key itself (deterministic)
    # In production, consider using a stored salt for better security
    salt = hashlib.sha256(secret_key.encode()).digest()[:16]
    
    # Derive a 32-byte key using PBKDF2
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    
    # Generate key from secret
    key_material = kdf.derive(secret_key.encode())
    _encryption_key = base64.urlsafe_b64encode(key_material)
    
    return _encryption_key


def encrypt_password(password: str) -> str:
    """
    Encrypt a password for storage in the database.
    
    Args:
        password: Plain text password to encrypt
        
    Returns:
        Encrypted password string (base64 encoded)
        
    Raises:
        ValueError: If FLASK_SECRET_KEY is not configured
    """
    try:
        key = _get_encryption_key()
        fernet = Fernet(key)
        encrypted = fernet.encrypt(password.encode('utf-8'))
        return encrypted.decode('utf-8')
    except Exception as e:
        logger.error(f"Error encrypting password: {e}", exc_info=True)
        raise ValueError(f"Failed to encrypt password: {str(e)}") from e


def decrypt_password(encrypted_password: str) -> str:
    """
    Decrypt a password from the database.
    
    Args:
        encrypted_password: Encrypted password string from database
        
    Returns:
        Plain text password
        
    Raises:
        ValueError: If decryption fails or FLASK_SECRET_KEY is not configured
    """
    try:
        key = _get_encryption_key()
        fernet = Fernet(key)
        decrypted = fernet.decrypt(encrypted_password.encode('utf-8'))
        return decrypted.decode('utf-8')
    except Exception as e:
        logger.error(f"Error decrypting password: {e}", exc_info=True)
        raise ValueError(f"Failed to decrypt password: {str(e)}") from e
