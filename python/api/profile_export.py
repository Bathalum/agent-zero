from python.helpers.api import ApiHandler, Request, Response


class ProfileExport(ApiHandler):
    """API endpoint for exporting profiles as ZIP packages."""
    
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
        Export a profile as a ZIP file.
        
        Input:
            profile_id: Profile to export
        
        Returns:
            ZIP file download response
        """
        profile_id = input.get("profile_id")
        
        if not profile_id:
            return Response(
                '{"error": "profile_id is required"}',
                status=400,
                mimetype="application/json"
            )
        
        try:
            import os
            import io
            import zipfile
            from python.helpers import files
            from flask import send_file
            
            profile_path = files.get_abs_path("agents", profile_id)
            
            if not os.path.exists(profile_path):
                return Response(
                    '{"error": "Profile not found"}',
                    status=404,
                    mimetype="application/json"
                )
            
            # Create in-memory ZIP file
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                # Walk through profile directory
                for root, dirs, files_list in os.walk(profile_path):
                    for filename in files_list:
                        file_path = os.path.join(root, filename)
                        arcname = os.path.relpath(file_path, profile_path)
                        zip_file.write(file_path, arcname)
            
            # Prepare for download
            zip_buffer.seek(0)
            
            return send_file(
                zip_buffer,
                mimetype="application/zip",
                as_attachment=True,
                download_name=f"{profile_id}_profile.zip"
            )
            
        except Exception as e:
            return Response(
                f'{{"error": "Failed to export profile: {str(e)}"}}',
                status=500,
                mimetype="application/json"
            )



