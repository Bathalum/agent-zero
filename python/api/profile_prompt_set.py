from python.helpers.api import ApiHandler, Request, Response


class ProfilePromptSet(ApiHandler):
    """API endpoint for writing profile prompt files."""
    
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
        Write a prompt file to a profile.
        Only custom profiles can be modified.
        
        Input:
            profile_id: Profile directory name
            prompt_file: Prompt filename (e.g., "agent.system.main.role.md")
            content: File content to write
        
        Returns:
            success: True if written successfully
            error: Error message if failed
        """
        profile_id = input.get("profile_id")
        prompt_file = input.get("prompt_file")
        content = input.get("content", "")
        
        if not profile_id or not prompt_file:
            return Response(
                '{"error": "profile_id and prompt_file are required"}',
                status=400,
                mimetype="application/json"
            )
        
        try:
            import os
            from python.helpers import files
            from python.helpers.profile_metadata import is_builtin_profile, update_profile_metadata
            
            # Safety check: prevent modifying built-in profiles
            if is_builtin_profile(profile_id):
                return Response(
                    '{"error": "Cannot modify built-in profiles. Duplicate the profile first."}',
                    status=400,
                    mimetype="application/json"
                )
            
            # Security: prevent directory traversal
            if ".." in prompt_file or "/" in prompt_file or "\\" in prompt_file:
                return Response(
                    '{"error": "Invalid prompt filename"}',
                    status=400,
                    mimetype="application/json"
                )
            
            # Ensure it's a markdown file
            if not prompt_file.endswith(".md"):
                return Response(
                    '{"error": "Prompt file must be a .md file"}',
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
            
            # Ensure prompts directory exists
            prompts_dir = os.path.join(profile_path, "prompts")
            os.makedirs(prompts_dir, exist_ok=True)
            
            # Write the file
            prompt_path = os.path.join(prompts_dir, prompt_file)
            with open(prompt_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            # Update modified timestamp
            from datetime import datetime
            update_profile_metadata(profile_id, {
                "modified_at": datetime.utcnow().isoformat() + "Z"
            })
            
            return {
                "success": True,
                "message": "Prompt file saved successfully"
            }
            
        except Exception as e:
            return Response(
                f'{{"error": "Failed to write prompt file: {str(e)}"}}',
                status=500,
                mimetype="application/json"
            )



