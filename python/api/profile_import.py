from python.helpers.api import ApiHandler, Request, Response


class ProfileImport(ApiHandler):
    """API endpoint for importing profiles from ZIP packages."""
    
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
        Import a profile from a ZIP file.
        
        Input:
            profile_id: New profile ID to import as
            zip_data: Base64-encoded ZIP file data
        
        Returns:
            success: True if imported successfully
            error: Error message if failed
        """
        profile_id = input.get("profile_id")
        zip_data = input.get("zip_data")
        
        if not profile_id or not zip_data:
            return Response(
                '{"error": "profile_id and zip_data are required"}',
                status=400,
                mimetype="application/json"
            )
        
        try:
            import os
            import io
            import base64
            import zipfile
            import shutil
            from python.helpers import files
            from python.helpers.profile_validator import validate_profile_name, validate_profile
            
            # Validate profile name
            is_valid, error_msg = validate_profile_name(profile_id)
            if not is_valid:
                return Response(
                    f'{{"error": "{error_msg}"}}',
                    status=400,
                    mimetype="application/json"
                )
            
            # Decode base64 ZIP data
            try:
                zip_bytes = base64.b64decode(zip_data)
            except Exception:
                return Response(
                    '{"error": "Invalid base64 data"}',
                    status=400,
                    mimetype="application/json"
                )
            
            profile_path = files.get_abs_path("agents", profile_id)
            
            # Create profile directory
            os.makedirs(profile_path, exist_ok=True)
            
            try:
                # Extract ZIP file
                with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zip_file:
                    # Security: check for path traversal in ZIP
                    for name in zip_file.namelist():
                        if name.startswith("/") or ".." in name:
                            raise Exception("Invalid file path in ZIP archive")
                    
                    # Extract all files
                    zip_file.extractall(profile_path)
                
                # Validate the imported profile
                is_valid, errors, warnings = validate_profile(profile_id)
                
                if not is_valid:
                    # Clean up on validation failure
                    shutil.rmtree(profile_path)
                    error_list = "; ".join(errors)
                    return Response(
                        f'{{"error": "Profile validation failed: {error_list}"}}',
                        status=400,
                        mimetype="application/json"
                    )
                
                # Update metadata to mark as custom
                from python.helpers.profile_metadata import update_profile_metadata
                from datetime import datetime
                
                update_profile_metadata(profile_id, {
                    "is_custom": True,
                    "created_at": datetime.utcnow().isoformat() + "Z",
                    "modified_at": datetime.utcnow().isoformat() + "Z"
                })
                
                return {
                    "success": True,
                    "profile_id": profile_id,
                    "warnings": warnings,
                    "message": "Profile imported successfully"
                }
                
            except zipfile.BadZipFile:
                # Clean up on error
                if os.path.exists(profile_path):
                    shutil.rmtree(profile_path)
                return Response(
                    '{"error": "Invalid ZIP file"}',
                    status=400,
                    mimetype="application/json"
                )
            except Exception as e:
                # Clean up on error
                if os.path.exists(profile_path):
                    shutil.rmtree(profile_path)
                raise e
            
        except Exception as e:
            return Response(
                f'{{"error": "Failed to import profile: {str(e)}"}}',
                status=500,
                mimetype="application/json"
            )



