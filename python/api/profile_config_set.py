from python.helpers.api import ApiHandler, Request, Response


class ProfileConfigSet(ApiHandler):
    """API endpoint for writing profile instruments.json configuration."""
    
    @classmethod
    def requires_auth(cls) -> bool:
        return False
    
    @classmethod
    def requires_csrf(cls) -> bool:
        return False
    
    @classmethod
    def requires_api_key(cls) -> bool:
        return False
    
    async def process(self, input: dict, request: Request) -> dict | Response:
        """
        Write instruments.json configuration to a profile.
        Only custom profiles can be modified.
        
        Input:
            profile_id: Profile directory name
            config: Configuration object to write
        
        Returns:
            success: True if written successfully
            error: Error message if failed
        """
        profile_id = input.get("profile_id")
        config = input.get("config")
        
        if not profile_id or not isinstance(config, dict):
            return Response(
                '{"error": "profile_id and config are required"}',
                status=400,
                mimetype="application/json"
            )
        
        try:
            import os
            import json
            from python.helpers import files
            from python.helpers.profile_metadata import is_builtin_profile, update_profile_metadata
            
            # Safety check: prevent modifying built-in profiles
            if is_builtin_profile(profile_id):
                return Response(
                    '{"error": "Cannot modify built-in profiles. Duplicate the profile first."}',
                    status=400,
                    mimetype="application/json"
                )
            
            profile_path = files.get_abs_path("agents", profile_id)
            if not os.path.exists(profile_path):
                return Response(
                    '{"error": "Profile not found"}',
                    status=404,
                    mimetype="application/json"
                )
            
            # Write the configuration
            instruments_path = os.path.join(profile_path, "instruments.json")
            with open(instruments_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
            
            # Update modified timestamp
            from datetime import datetime
            update_profile_metadata(profile_id, {
                "modified_at": datetime.utcnow().isoformat() + "Z"
            })
            
            return {
                "success": True,
                "message": "Configuration saved successfully"
            }
            
        except Exception as e:
            return Response(
                f'{{"error": "Failed to write configuration: {str(e)}"}}',
                status=500,
                mimetype="application/json"
            )



