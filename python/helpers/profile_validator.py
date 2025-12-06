"""
Profile validation module.
Validates profile structure, files, and configuration to ensure integrity.
"""

import json
import os
from typing import Any
from python.helpers import files
from python.helpers.profile_metadata import BUILTIN_PROFILES


class ProfileValidationError(Exception):
    """Exception raised for profile validation errors."""
    pass


class ProfileValidator:
    """Validates profile structure and contents."""
    
    def __init__(self, profile_id: str):
        """
        Initialize validator for a profile.
        
        Args:
            profile_id: The profile directory name
        """
        self.profile_id = profile_id
        self.profile_path = files.get_abs_path("agents", profile_id)
        self.errors: list[str] = []
        self.warnings: list[str] = []
    
    def validate_all(self) -> tuple[bool, list[str], list[str]]:
        """
        Run all validation checks.
        
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []
        
        # Run all validation checks
        self._validate_profile_exists()
        self._validate_context_file()
        self._validate_prompt_files()
        self._validate_profile_json()
        self._validate_instruments_json()
        self._validate_extensions()
        self._validate_tools()
        self._validate_no_builtin_conflict()
        
        return len(self.errors) == 0, self.errors, self.warnings
    
    def _validate_profile_exists(self):
        """Check if profile directory exists."""
        if not os.path.exists(self.profile_path):
            self.errors.append(f"Profile directory not found: {self.profile_path}")
    
    def _validate_context_file(self):
        """Validate _context.md file."""
        context_path = os.path.join(self.profile_path, "_context.md")
        if not os.path.exists(context_path):
            self.errors.append("Missing required file: _context.md")
        else:
            try:
                with open(context_path, "r", encoding="utf-8") as f:
                    content = f.read()
                if not content.strip():
                    self.warnings.append("_context.md is empty")
            except Exception as e:
                self.errors.append(f"Cannot read _context.md: {str(e)}")
    
    def _validate_prompt_files(self):
        """Validate prompt files are valid markdown."""
        prompts_dir = os.path.join(self.profile_path, "prompts")
        if not os.path.exists(prompts_dir):
            self.warnings.append("No prompts directory found")
            return
        
        # Check for at least one prompt file
        prompt_files = [f for f in os.listdir(prompts_dir) if f.endswith(".md")]
        if not prompt_files:
            self.warnings.append("No prompt files found in prompts directory")
        
        # Validate each prompt file
        for filename in prompt_files:
            filepath = os.path.join(prompts_dir, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                if not content.strip():
                    self.warnings.append(f"Prompt file is empty: {filename}")
            except Exception as e:
                self.errors.append(f"Cannot read prompt file {filename}: {str(e)}")
    
    def _validate_profile_json(self):
        """Validate profile.json if it exists."""
        profile_json_path = os.path.join(self.profile_path, "profile.json")
        if not os.path.exists(profile_json_path):
            # profile.json is optional
            return
        
        try:
            with open(profile_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Validate structure
            if not isinstance(data, dict):
                self.errors.append("profile.json must be a JSON object")
                return
            
            # Validate optional fields
            if "enabled_extensions" in data and not isinstance(data["enabled_extensions"], list):
                self.errors.append("profile.json: enabled_extensions must be an array")
            
            if "enabled_instruments" in data and not isinstance(data["enabled_instruments"], list):
                self.errors.append("profile.json: enabled_instruments must be an array")
            
            if "instrument_config" in data and not isinstance(data["instrument_config"], dict):
                self.errors.append("profile.json: instrument_config must be an object")
            
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON in profile.json: {str(e)}")
        except Exception as e:
            self.errors.append(f"Cannot read profile.json: {str(e)}")
    
    def _validate_instruments_json(self):
        """Validate instruments.json if it exists."""
        instruments_path = os.path.join(self.profile_path, "instruments.json")
        if not os.path.exists(instruments_path):
            # instruments.json is optional
            return
        
        try:
            with open(instruments_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Validate structure
            if not isinstance(data, dict):
                self.errors.append("instruments.json must be a JSON object")
                return
            
            # Validate expected fields
            if "enabled" in data and not isinstance(data["enabled"], bool):
                self.warnings.append("instruments.json: enabled should be a boolean")
            
            if "recall_interval" in data and not isinstance(data["recall_interval"], (int, float)):
                self.warnings.append("instruments.json: recall_interval should be a number")
            
            if "max_instruments" in data and not isinstance(data["max_instruments"], int):
                self.warnings.append("instruments.json: max_instruments should be an integer")
            
            if "similarity_threshold" in data and not isinstance(data["similarity_threshold"], (int, float)):
                self.warnings.append("instruments.json: similarity_threshold should be a number")
            
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON in instruments.json: {str(e)}")
        except Exception as e:
            self.errors.append(f"Cannot read instruments.json: {str(e)}")
    
    def _validate_extensions(self):
        """Validate extensions directory and files."""
        extensions_dir = os.path.join(self.profile_path, "extensions")
        if not os.path.exists(extensions_dir):
            # Extensions are optional
            return
        
        # Walk through extensions directory
        for root, dirs, files_list in os.walk(extensions_dir):
            for filename in files_list:
                if filename.endswith(".py"):
                    filepath = os.path.join(root, filename)
                    try:
                        # Try to read the file
                        with open(filepath, "r", encoding="utf-8") as f:
                            content = f.read()
                        
                        # Basic Python syntax check (very simple)
                        if not content.strip():
                            self.warnings.append(f"Extension file is empty: {filename}")
                        
                        # Check for common Python patterns
                        if "def " not in content and "class " not in content:
                            self.warnings.append(f"Extension file may not contain valid Python: {filename}")
                        
                    except Exception as e:
                        self.errors.append(f"Cannot read extension file {filename}: {str(e)}")
    
    def _validate_tools(self):
        """Validate tools directory and files."""
        tools_dir = os.path.join(self.profile_path, "tools")
        if not os.path.exists(tools_dir):
            # Tools are optional
            return
        
        # Check tool files
        for filename in os.listdir(tools_dir):
            if filename.endswith(".py"):
                filepath = os.path.join(tools_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    if not content.strip():
                        self.warnings.append(f"Tool file is empty: {filename}")
                    
                    # Check for Tool class pattern
                    if "class " not in content:
                        self.warnings.append(f"Tool file may not contain a Tool class: {filename}")
                    
                except Exception as e:
                    self.errors.append(f"Cannot read tool file {filename}: {str(e)}")
    
    def _validate_no_builtin_conflict(self):
        """Check that profile ID doesn't conflict with built-in profiles."""
        if self.profile_id in BUILTIN_PROFILES:
            # Get profile metadata to check if it's actually custom
            from python.helpers.profile_metadata import get_profile_metadata
            metadata = get_profile_metadata(self.profile_id)
            if metadata.get("is_custom", False):
                self.errors.append(
                    f"Profile ID '{self.profile_id}' conflicts with built-in profile name"
                )


def validate_profile(profile_id: str) -> tuple[bool, list[str], list[str]]:
    """
    Convenience function to validate a profile.
    
    Args:
        profile_id: The profile directory name
        
    Returns:
        Tuple of (is_valid, errors, warnings)
    """
    validator = ProfileValidator(profile_id)
    return validator.validate_all()


def validate_profile_name(profile_id: str) -> tuple[bool, str]:
    """
    Validate that a profile name is acceptable for creation.
    
    Args:
        profile_id: Proposed profile ID
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check for empty name
    if not profile_id or not profile_id.strip():
        return False, "Profile name cannot be empty"
    
    # Check for valid characters (alphanumeric, underscore, hyphen)
    import re
    if not re.match(r'^[a-zA-Z0-9_-]+$', profile_id):
        return False, "Profile name can only contain letters, numbers, underscores, and hyphens"
    
    # Check if it conflicts with built-in
    if profile_id in BUILTIN_PROFILES:
        return False, f"Profile name '{profile_id}' is reserved (built-in profile)"
    
    # Check if it already exists
    profile_path = files.get_abs_path("agents", profile_id)
    if os.path.exists(profile_path):
        return False, "A profile with this name already exists"
    
    return True, ""



