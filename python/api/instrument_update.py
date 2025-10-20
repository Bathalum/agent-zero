from python.helpers.api import ApiHandler, Request, Response
from python.helpers.instrument_metadata import InstrumentMetadata
import json


class InstrumentUpdate(ApiHandler):
    """API endpoint for updating instrument metadata."""
    
    @classmethod
    def requires_auth(cls) -> bool:
        return False  # No web auth required
    
    @classmethod
    def requires_csrf(cls) -> bool:
        return False  # No CSRF required
    
    @classmethod
    def requires_api_key(cls) -> bool:
        return True  # Require API key for updates
    
    async def process(self, input: dict, request: Request) -> dict | Response:
        """
        Update metadata for an existing instrument.
        
        Parameters:
        - instrument_id: str (required) - Unique instrument identifier
        - profiles: list[str] (optional) - List of profile names
        - tags: list[str] (optional) - List of tags
        - priority: int (optional) - Priority level (lower = higher precedence)
        - enabled: bool (optional) - Whether instrument is enabled
        - metadata: dict (optional) - Additional metadata (display_name, category, etc.)
        """
        # Extract and validate instrument_id
        instrument_id = input.get("instrument_id", "").strip()
        
        if not instrument_id:
            return Response(
                '{"error": "instrument_id is required"}',
                status=400,
                mimetype="application/json"
            )
        
        # Check if instrument exists
        existing = InstrumentMetadata.get_instrument_metadata(instrument_id)
        if not existing:
            return Response(
                f'{{"error": "Instrument \'{instrument_id}\' not found"}}',
                status=404,
                mimetype="application/json"
            )
        
        try:
            # Build updates dictionary from provided parameters
            updates = {}
            
            if "profiles" in input:
                profiles = input["profiles"]
                if isinstance(profiles, str):
                    # Handle comma-separated string
                    profiles = [p.strip() for p in profiles.split(",") if p.strip()]
                elif not isinstance(profiles, list):
                    return Response(
                        '{"error": "profiles must be a list or comma-separated string"}',
                        status=400,
                        mimetype="application/json"
                    )
                updates["profiles"] = profiles
            
            if "tags" in input:
                tags = input["tags"]
                if isinstance(tags, str):
                    # Handle comma-separated string
                    tags = [t.strip() for t in tags.split(",") if t.strip()]
                elif not isinstance(tags, list):
                    return Response(
                        '{"error": "tags must be a list or comma-separated string"}',
                        status=400,
                        mimetype="application/json"
                    )
                updates["tags"] = tags
            
            if "priority" in input:
                try:
                    priority = int(input["priority"])
                    if priority < 1 or priority > 100:
                        return Response(
                            '{"error": "priority must be between 1 and 100"}',
                            status=400,
                            mimetype="application/json"
                        )
                    updates["priority"] = priority
                except (ValueError, TypeError):
                    return Response(
                        '{"error": "priority must be a valid integer"}',
                        status=400,
                        mimetype="application/json"
                    )
            
            if "enabled" in input:
                enabled = input["enabled"]
                if isinstance(enabled, str):
                    enabled = enabled.lower() in ("true", "1", "yes", "on")
                elif not isinstance(enabled, bool):
                    return Response(
                        '{"error": "enabled must be a boolean"}',
                        status=400,
                        mimetype="application/json"
                    )
                updates["enabled"] = enabled
            
            if "metadata" in input:
                metadata = input["metadata"]
                if not isinstance(metadata, dict):
                    return Response(
                        '{"error": "metadata must be a dictionary"}',
                        status=400,
                        mimetype="application/json"
                    )
                updates["metadata"] = metadata
            
            # Additional direct metadata fields
            if "display_name" in input:
                if "metadata" not in updates:
                    updates["metadata"] = {}
                updates["metadata"]["display_name"] = str(input["display_name"])
            
            if "category" in input:
                if "metadata" not in updates:
                    updates["metadata"] = {}
                updates["metadata"]["category"] = str(input["category"])
            
            # Perform update
            if not updates:
                return Response(
                    '{"error": "No valid update fields provided"}',
                    status=400,
                    mimetype="application/json"
                )
            
            updated = InstrumentMetadata.update_instrument_metadata(instrument_id, updates)
            
            if updated is None:
                return Response(
                    f'{{"error": "Failed to update instrument \'{instrument_id}\'"}}',
                    status=500,
                    mimetype="application/json"
                )
            
            return {
                "success": True,
                "message": f"Instrument '{instrument_id}' updated successfully",
                "instrument_id": instrument_id,
                "updated_fields": list(updates.keys()),
                "instrument": {
                    "id": instrument_id,
                    **updated
                }
            }
            
        except Exception as e:
            return Response(
                f'{{"error": "Failed to update instrument: {str(e)}"}}',
                status=500,
                mimetype="application/json"
            )

