from python.helpers.api import ApiHandler, Request, Response


class ProfileCreate(ApiHandler):
    """API endpoint for creating new profiles (duplicate or blank)."""
    
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
        Create a new profile by duplicating an existing one or creating blank.
        
        Input:
            profile_id: New profile ID (directory name)
            source_id: (optional) Profile to duplicate from
            metadata: (optional) Custom metadata for the new profile
        
        Returns:
            success: True if created
            profile_id: The new profile ID
            error: Error message if failed
        """
        profile_id = input.get("profile_id")
        source_id = input.get("source_id")
        metadata = input.get("metadata") or {}
        
        if not profile_id:
            return Response(
                '{"error": "profile_id is required"}',
                status=400,
                mimetype="application/json"
            )
        
        try:
            from python.helpers.profile_metadata import (
                duplicate_profile,
                create_blank_profile
            )
            from python.helpers.profile_validator import validate_profile_name
            
            # Validate profile name
            is_valid, error_msg = validate_profile_name(profile_id)
            if not is_valid:
                return Response(
                    f'{{"error": "{error_msg}"}}',
                    status=400,
                    mimetype="application/json"
                )
            
            # Create profile
            if source_id:
                # Duplicate from source
                success = duplicate_profile(source_id, profile_id, metadata)
                if not success:
                    return Response(
                        '{"error": "Failed to duplicate profile. Source may not exist or target already exists."}',
                        status=400,
                        mimetype="application/json"
                    )
            else:
                # Create blank profile
                success = create_blank_profile(profile_id, metadata)
                if not success:
                    return Response(
                        '{"error": "Failed to create profile. Profile may already exist."}',
                        status=400,
                        mimetype="application/json"
                    )
            
            return {
                "success": True,
                "profile_id": profile_id,
                "message": "Profile created successfully"
            }
            
        except Exception as e:
            return Response(
                f'{{"error": "Failed to create profile: {str(e)}"}}',
                status=500,
                mimetype="application/json"
            )



