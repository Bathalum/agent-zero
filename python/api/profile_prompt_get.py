from python.helpers.api import ApiHandler, Request, Response


class ProfilePromptGet(ApiHandler):
    """API endpoint for reading profile prompt files."""
    
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
        Read a prompt file from a profile.
        
        Input:
            profile_id: Profile directory name
            prompt_file: Prompt filename (e.g., "agent.system.main.role.md")
        
        Returns:
            success: True if read successfully
            content: File content
            error: Error message if failed
        """
        profile_id = input.get("profile_id")
        prompt_file = input.get("prompt_file")
        
        if not profile_id or not prompt_file:
            return Response(
                '{"error": "profile_id and prompt_file are required"}',
                status=400,
                mimetype="application/json"
            )
        
        try:
            import os
            from python.helpers import files
            
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
            
            prompt_path = files.get_abs_path("agents", profile_id, "prompts", prompt_file)
            
            if not os.path.exists(prompt_path):
                return Response(
                    '{"error": "Prompt file not found"}',
                    status=404,
                    mimetype="application/json"
                )
            
            # Read the file
            with open(prompt_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            return {
                "success": True,
                "content": content
            }
            
        except Exception as e:
            return Response(
                f'{{"error": "Failed to read prompt file: {str(e)}"}}',
                status=500,
                mimetype="application/json"
            )



