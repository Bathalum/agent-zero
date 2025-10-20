"""
Instrument Metadata Management Module

Handles central metadata registry for instruments including:
- Loading/saving central metadata registry
- Getting instruments by profile
- Getting instruments by tag
- Adding/updating/removing instrument metadata
- Validating metadata structure
- Backward compatibility handling
"""

import json
import os
from pathlib import Path
from typing import Any
from python.helpers import files


METADATA_FILE = "instruments/metadata.json"


class InstrumentMetadata:
    """Manages instrument metadata registry"""
    
    @staticmethod
    def load_registry() -> dict:
        """
        Load the central metadata registry.
        Returns empty registry structure if file doesn't exist.
        """
        registry_path = files.get_abs_path(METADATA_FILE)
        
        if not os.path.exists(registry_path):
            return {
                "version": "1.0",
                "instruments": {}
            }
        
        try:
            with open(registry_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Ensure proper structure
                if "version" not in data:
                    data["version"] = "1.0"
                if "instruments" not in data:
                    data["instruments"] = {}
                return data
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load instrument metadata: {e}")
            return {
                "version": "1.0",
                "instruments": {}
            }
    
    @staticmethod
    def save_registry(data: dict) -> None:
        """
        Save the central metadata registry.
        Creates directory if it doesn't exist.
        """
        registry_path = files.get_abs_path(METADATA_FILE)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(registry_path), exist_ok=True)
        
        # Validate structure
        if "version" not in data:
            data["version"] = "1.0"
        if "instruments" not in data:
            data["instruments"] = {}
        
        try:
            with open(registry_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Error: Could not save instrument metadata: {e}")
            raise
    
    @staticmethod
    def get_instrument_metadata(instrument_id: str) -> dict | None:
        """
        Get metadata for a specific instrument by ID.
        Returns None if instrument not found.
        """
        registry = InstrumentMetadata.load_registry()
        return registry.get("instruments", {}).get(instrument_id)
    
    @staticmethod
    def set_instrument_metadata(instrument_id: str, metadata: dict) -> None:
        """
        Set or update metadata for a specific instrument.
        
        Args:
            instrument_id: Unique identifier for the instrument (e.g., "n8n.slack_message")
            metadata: Dictionary containing instrument metadata
        """
        registry = InstrumentMetadata.load_registry()
        
        # Ensure default values
        defaults = {
            "type": "unknown",
            "source_path": "",
            "profiles": ["default"],
            "tags": [],
            "priority": 5,
            "enabled": True,
            "metadata": {}
        }
        
        # Merge with defaults
        instrument_data = {**defaults, **metadata}
        
        # Store in registry
        if "instruments" not in registry:
            registry["instruments"] = {}
        
        registry["instruments"][instrument_id] = instrument_data
        
        # Save registry
        InstrumentMetadata.save_registry(registry)
    
    @staticmethod
    def update_instrument_metadata(instrument_id: str, updates: dict) -> dict | None:
        """
        Partially update metadata for an existing instrument.
        Only provided fields are updated.
        
        Returns updated metadata or None if instrument not found.
        """
        registry = InstrumentMetadata.load_registry()
        
        if instrument_id not in registry.get("instruments", {}):
            return None
        
        # Update only provided fields
        current = registry["instruments"][instrument_id]
        
        # Handle nested metadata updates
        if "metadata" in updates:
            if "metadata" not in current:
                current["metadata"] = {}
            current["metadata"].update(updates["metadata"])
            updates = {k: v for k, v in updates.items() if k != "metadata"}
        
        current.update(updates)
        registry["instruments"][instrument_id] = current
        
        # Save registry
        InstrumentMetadata.save_registry(registry)
        
        return current
    
    @staticmethod
    def delete_instrument_metadata(instrument_id: str) -> bool:
        """
        Delete metadata for a specific instrument.
        Returns True if deleted, False if not found.
        """
        registry = InstrumentMetadata.load_registry()
        
        if instrument_id in registry.get("instruments", {}):
            del registry["instruments"][instrument_id]
            InstrumentMetadata.save_registry(registry)
            return True
        
        return False
    
    @staticmethod
    def get_instruments_by_profile(profile: str) -> list[dict]:
        """
        Get all instruments assigned to a specific profile.
        
        Args:
            profile: Profile name (e.g., "researcher", "developer", "default")
        
        Returns:
            List of instrument metadata dictionaries
        """
        registry = InstrumentMetadata.load_registry()
        results = []
        
        for instrument_id, metadata in registry.get("instruments", {}).items():
            profiles = metadata.get("profiles", ["default"])
            if profile in profiles:
                results.append({
                    "id": instrument_id,
                    **metadata
                })
        
        # Sort by priority (lower priority = higher precedence)
        results.sort(key=lambda x: x.get("priority", 5))
        
        return results
    
    @staticmethod
    def get_instruments_by_tags(tags: list[str], match_all: bool = False) -> list[dict]:
        """
        Get all instruments that have specific tags.
        
        Args:
            tags: List of tags to filter by
            match_all: If True, instrument must have ALL tags; if False, ANY tag
        
        Returns:
            List of instrument metadata dictionaries
        """
        registry = InstrumentMetadata.load_registry()
        results = []
        
        for instrument_id, metadata in registry.get("instruments", {}).items():
            instrument_tags = metadata.get("tags", [])
            
            if match_all:
                # Must have all tags
                if all(tag in instrument_tags for tag in tags):
                    results.append({
                        "id": instrument_id,
                        **metadata
                    })
            else:
                # Must have at least one tag
                if any(tag in instrument_tags for tag in tags):
                    results.append({
                        "id": instrument_id,
                        **metadata
                    })
        
        # Sort by priority
        results.sort(key=lambda x: x.get("priority", 5))
        
        return results
    
    @staticmethod
    def list_all_instruments() -> list[dict]:
        """
        List all registered instruments.
        
        Returns:
            List of instrument metadata dictionaries
        """
        registry = InstrumentMetadata.load_registry()
        results = []
        
        for instrument_id, metadata in registry.get("instruments", {}).items():
            results.append({
                "id": instrument_id,
                **metadata
            })
        
        # Sort by priority
        results.sort(key=lambda x: x.get("priority", 5))
        
        return results
    
    @staticmethod
    def extract_instrument_id_from_path(path: str) -> str | None:
        """
        Extract instrument ID from file path.
        
        Examples:
            'instruments/custom/n8n/workflows/slack_message.md' -> 'n8n.slack_message'
            '/a0/instruments/custom/n8n/workflows/email.md' -> 'n8n.email'
        
        Args:
            path: File path string
        
        Returns:
            Instrument ID string or None if cannot be extracted
        """
        # Normalize path separators
        path = path.replace("\\", "/")
        
        # Check if it's an n8n workflow
        if "n8n" in path and path.endswith(".md"):
            # Extract filename without extension
            filename = os.path.basename(path).replace(".md", "")
            return f"n8n.{filename}"
        
        # Add support for other instrument types here as needed
        
        return None
    
    @staticmethod
    def get_all_profiles() -> list[str]:
        """
        Get list of all unique profiles assigned to instruments.
        
        Returns:
            List of profile names
        """
        registry = InstrumentMetadata.load_registry()
        profiles = set()
        
        for metadata in registry.get("instruments", {}).values():
            profiles.update(metadata.get("profiles", ["default"]))
        
        return sorted(list(profiles))
    
    @staticmethod
    def get_all_tags() -> list[str]:
        """
        Get list of all unique tags assigned to instruments.
        
        Returns:
            List of tag names
        """
        registry = InstrumentMetadata.load_registry()
        tags = set()
        
        for metadata in registry.get("instruments", {}).values():
            tags.update(metadata.get("tags", []))
        
        return sorted(list(tags))


def extract_instrument_id_from_path(path: str) -> str | None:
    """Convenience wrapper for InstrumentMetadata.extract_instrument_id_from_path"""
    return InstrumentMetadata.extract_instrument_id_from_path(path)

