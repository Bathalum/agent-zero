"""
Profile metadata helper functions.
Provides utility functions for profile management without modifying core agent logic.
"""

import json
import os
import shutil
from datetime import datetime
from typing import Any
from python.helpers import files


# Built-in profiles that cannot be modified through UI
BUILTIN_PROFILES = ["agent0", "default", "developer", "researcher", "hacker"]


def is_builtin_profile(profile_id: str) -> bool:
    """Check if a profile is a built-in profile (read-only in UI)."""
    return profile_id in BUILTIN_PROFILES


def get_profile_metadata(profile_id: str) -> dict[str, Any]:
    """
    Load profile metadata from profile.json with sensible defaults.
    
    Args:
        profile_id: The profile directory name
        
    Returns:
        Dictionary containing profile metadata
    """
    profile_path = files.get_abs_path("agents", profile_id)
    profile_json_path = os.path.join(profile_path, "profile.json")
    
    # Default metadata structure
    defaults = {
        "display_name": profile_id.replace("_", " ").title(),
        "description": "",
        "avatar_icon": "default",
        "avatar_color": "#4A90E2",
        "category": "General",
        "is_custom": not is_builtin_profile(profile_id),
        "base_profile": None,
        "enabled_extensions": [],
        "enabled_instruments": [],
        "instrument_config": {
            "enabled": False,
            "recall_interval": 5,
            "max_instruments": 2,
            "similarity_threshold": 0.4
        },
        "created_at": None,
        "modified_at": None
    }
    
    # Load existing metadata if available
    if os.path.exists(profile_json_path):
        try:
            with open(profile_json_path, "r", encoding="utf-8") as f:
                custom_meta = json.load(f)
            defaults.update(custom_meta)
        except Exception:
            pass  # Use defaults on error
    
    return defaults


def update_profile_metadata(profile_id: str, metadata: dict[str, Any]) -> bool:
    """
    Update profile metadata in profile.json.
    
    Args:
        profile_id: The profile directory name
        metadata: Dictionary of metadata to update
        
    Returns:
        True if successful, False otherwise
    """
    try:
        profile_path = files.get_abs_path("agents", profile_id)
        if not os.path.exists(profile_path):
            return False
        
        profile_json_path = os.path.join(profile_path, "profile.json")
        
        # Load existing or start with defaults
        existing = get_profile_metadata(profile_id)
        
        # Update with new metadata
        existing.update(metadata)
        existing["modified_at"] = datetime.utcnow().isoformat() + "Z"
        
        # Write back to file
        with open(profile_json_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2)
        
        return True
    except Exception:
        return False


def list_available_profiles() -> list[dict[str, Any]]:
    """
    Get all available profiles with their metadata.
    
    Returns:
        List of profile dictionaries with metadata
    """
    profile_dirs = files.get_subdirectories("agents", exclude=["_example"])
    profiles = []
    
    for profile_id in profile_dirs:
        try:
            metadata = get_profile_metadata(profile_id)
            
            # Add description from _context.md if not in metadata
            if not metadata.get("description"):
                context_path = files.get_abs_path("agents", profile_id, "_context.md")
                if files.exists(context_path):
                    context = files.read_file(context_path)
                    for line in context.split("\n"):
                        line = line.strip()
                        if line and not line.startswith("#"):
                            metadata["description"] = line
                            break
            
            profiles.append({
                "id": profile_id,
                **metadata
            })
        except Exception:
            # Fallback for profiles without proper metadata
            profiles.append({
                "id": profile_id,
                "display_name": profile_id.replace("_", " ").title(),
                "description": f"{profile_id} agent profile",
                "is_custom": not is_builtin_profile(profile_id),
            })
    
    return sorted(profiles, key=lambda p: p["id"])


def duplicate_profile(source_id: str, target_id: str, metadata: dict[str, Any] | None = None) -> bool:
    """
    Duplicate a profile (built-in or custom) to create a new custom profile.
    
    Args:
        source_id: Source profile to copy from
        target_id: New profile ID (directory name)
        metadata: Optional metadata for the new profile
        
    Returns:
        True if successful, False otherwise
    """
    try:
        source_path = files.get_abs_path("agents", source_id)
        target_path = files.get_abs_path("agents", target_id)
        
        # Check if source exists
        if not os.path.exists(source_path):
            return False
        
        # Check if target already exists
        if os.path.exists(target_path):
            return False
        
        # Copy entire profile directory
        shutil.copytree(source_path, target_path)
        
        # Update metadata for new profile
        new_metadata = metadata or {}
        new_metadata.update({
            "is_custom": True,
            "base_profile": source_id,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "modified_at": datetime.utcnow().isoformat() + "Z"
        })
        
        # Set display name if not provided
        if "display_name" not in new_metadata:
            new_metadata["display_name"] = target_id.replace("_", " ").title()
        
        # Save metadata
        update_profile_metadata(target_id, new_metadata)
        
        return True
    except Exception:
        # Clean up on failure
        target_path = files.get_abs_path("agents", target_id)
        if os.path.exists(target_path):
            try:
                shutil.rmtree(target_path)
            except Exception:
                pass
        return False


def delete_profile(profile_id: str, force: bool = False) -> tuple[bool, str]:
    """
    Delete a custom profile.
    
    Args:
        profile_id: Profile to delete
        force: If True, skip safety checks (use with caution)
        
    Returns:
        Tuple of (success, error_message)
    """
    # Safety check: prevent deleting built-in profiles
    if not force and is_builtin_profile(profile_id):
        return False, "Cannot delete built-in profiles"
    
    try:
        profile_path = files.get_abs_path("agents", profile_id)
        
        if not os.path.exists(profile_path):
            return False, "Profile not found"
        
        # Remove directory
        shutil.rmtree(profile_path)
        
        return True, ""
    except Exception as e:
        return False, str(e)


def create_blank_profile(profile_id: str, metadata: dict[str, Any] | None = None) -> bool:
    """
    Create a new blank profile with minimal structure.
    
    Args:
        profile_id: New profile ID (directory name)
        metadata: Optional metadata for the profile
        
    Returns:
        True if successful, False otherwise
    """
    try:
        profile_path = files.get_abs_path("agents", profile_id)
        
        # Check if already exists
        if os.path.exists(profile_path):
            return False
        
        # Create directory structure
        os.makedirs(profile_path, exist_ok=True)
        os.makedirs(os.path.join(profile_path, "prompts"), exist_ok=True)
        os.makedirs(os.path.join(profile_path, "extensions"), exist_ok=True)
        os.makedirs(os.path.join(profile_path, "tools"), exist_ok=True)
        
        # Create _context.md
        context_content = metadata.get("description", f"Custom agent profile: {profile_id}") if metadata else f"Custom agent profile: {profile_id}"
        with open(os.path.join(profile_path, "_context.md"), "w", encoding="utf-8") as f:
            f.write(f"# {profile_id.replace('_', ' ').title()}\n\n{context_content}\n")
        
        # Create basic role prompt
        role_prompt = """# Agent Role

You are a helpful AI assistant.

## Capabilities

- Answer questions
- Assist with tasks
- Provide information

## Approach

Be helpful, accurate, and clear in your responses.
"""
        with open(os.path.join(profile_path, "prompts", "agent.system.main.role.md"), "w", encoding="utf-8") as f:
            f.write(role_prompt)
        
        # Set metadata
        new_metadata = metadata or {}
        new_metadata.update({
            "is_custom": True,
            "base_profile": None,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "modified_at": datetime.utcnow().isoformat() + "Z"
        })
        
        if "display_name" not in new_metadata:
            new_metadata["display_name"] = profile_id.replace("_", " ").title()
        
        update_profile_metadata(profile_id, new_metadata)
        
        return True
    except Exception:
        # Clean up on failure
        try:
            profile_path = files.get_abs_path("agents", profile_id)
            if os.path.exists(profile_path):
                shutil.rmtree(profile_path)
        except Exception:
            pass
        return False



