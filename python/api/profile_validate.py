from python.helpers.api import ApiHandler, Request, Response


class ProfileValidate(ApiHandler):
    """API endpoint for validating profile structure and contents."""
    
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
        Validate a profile's structure and files.
        
        Input:
            profile_id: Profile to validate
        
        Returns:
            success: True if validation passed
            is_valid: True if profile is valid
            errors: List of error messages
            warnings: List of warning messages
        """
        profile_id = input.get("profile_id")
        
        if not profile_id:
            return Response(
                '{"error": "profile_id is required"}',
                status=400,
                mimetype="application/json"
            )
        
        try:
            from python.helpers.profile_validator import validate_profile
            
            is_valid, errors, warnings = validate_profile(profile_id)
            
            return {
                "success": True,
                "is_valid": is_valid,
                "errors": errors,
                "warnings": warnings
            }
            
        except Exception as e:
            return Response(
                f'{{"error": "Failed to validate profile: {str(e)}"}}',
                status=500,
                mimetype="application/json"
            )



