from python.helpers.api import ApiHandler, Request, Response


class ProfileDelete(ApiHandler):
    """API endpoint for deleting custom profiles."""
    
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
        Delete a custom profile.
        Built-in profiles cannot be deleted.
        
        Input:
            profile_id: Profile to delete
        
        Returns:
            success: True if deleted
            error: Error message if failed
        """
        profile_id = input.get("profile_id")
        
        if not profile_id:
            return Response(
                '{"error": "profile_id is required"}',
                status=400,
                mimetype="application/json"
            )
        
        try:
            from python.helpers.profile_metadata import delete_profile, is_builtin_profile
            from python.helpers import settings
            
            # Safety check: prevent deleting built-in profiles
            if is_builtin_profile(profile_id):
                return Response(
                    '{"error": "Cannot delete built-in profiles"}',
                    status=400,
                    mimetype="application/json"
                )
            
            # Check if this is the currently active profile
            current_settings = settings.get_settings()
            current_profile = current_settings.get("agent_profile")
            if current_profile == profile_id:
                return Response(
                    '{"error": "Cannot delete the currently active profile. Switch to another profile first."}',
                    status=400,
                    mimetype="application/json"
                )
            
            # Delete the profile
            success, error_msg = delete_profile(profile_id)
            
            if not success:
                return Response(
                    f'{{"error": "{error_msg}"}}',
                    status=400,
                    mimetype="application/json"
                )
            
            return {
                "success": True,
                "message": "Profile deleted successfully"
            }
            
        except Exception as e:
            return Response(
                f'{{"error": "Failed to delete profile: {str(e)}"}}',
                status=500,
                mimetype="application/json"
            )



