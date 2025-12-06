#!/usr/bin/env python3
"""
N8N Workflow Bridge
Executes n8n workflows via webhooks with robust error handling and clean output.
Uses only Python standard library (no external dependencies).
"""

import sys
import json
import time
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import os
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import urllib.parse


class N8NBridge:
    """Bridge for executing n8n workflows via webhooks."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the bridge with configuration."""
        if config_path is None:
            config_path = Path(__file__).parent / "config.json"
        else:
            config_path = Path(config_path)
            
        self.config = self._load_config(config_path)
        self.timeout = 30  # Default timeout in seconds
        self.max_retries = 3
        self.retry_delays = [1, 2, 4]  # Exponential backoff delays
        
    def _load_config(self, config_path: Path) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            if not config_path.exists():
                return {
                    "n8n_base_url": "https://your-n8n-instance.com",
                    "workflows": {}
                }
            
            with open(config_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"✗ Config Error: Invalid JSON in {config_path}: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"✗ Config Error: Failed to load {config_path}: {e}")
            sys.exit(1)
    
    def _get_workflow_config(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific workflow."""
        return self.config.get("workflows", {}).get(workflow_id)
    
    def _build_webhook_url(self, workflow_id: str) -> Optional[str]:
        """Build the full webhook URL for a workflow."""
        workflow_config = self._get_workflow_config(workflow_id)
        if not workflow_config:
            return None
            
        base_url = self.config.get("n8n_base_url", "").rstrip("/")
        webhook_path = workflow_config.get("webhook_path", "").lstrip("/")
        
        if not base_url or not webhook_path:
            return None
            
        return f"{base_url}/{webhook_path}"
    
    def _format_success(self, workflow_id: str, result: Any) -> str:
        """Format successful response for Agent Zero."""
        workflow_config = self._get_workflow_config(workflow_id)
        workflow_name = workflow_config.get("description", workflow_id) if workflow_config else workflow_id
        
        # Extract meaningful information from result
        if isinstance(result, dict):
            # Common n8n response patterns
            if "message" in result:
                return f"✓ {workflow_name}: {result['message']}"
            elif "data" in result:
                data = result["data"]
                if isinstance(data, dict):
                    # Try to extract key information
                    summary_parts = []
                    for key in ["status", "id", "result"]:
                        if key in data:
                            summary_parts.append(f"{key}: {data[key]}")
                    if summary_parts:
                        return f"✓ {workflow_name}: {', '.join(summary_parts)}"
                return f"✓ {workflow_name}: Success"
            elif "success" in result and result["success"]:
                return f"✓ {workflow_name}: Operation completed successfully"
        
        # Default success message
        return f"✓ {workflow_name}: Workflow executed successfully"
    
    def _format_error(self, workflow_id: str, error: str) -> str:
        """Format error message for Agent Zero."""
        workflow_config = self._get_workflow_config(workflow_id)
        workflow_name = workflow_config.get("description", workflow_id) if workflow_config else workflow_id
        
        # Clean up error message
        error = error.strip()
        if len(error) > 200:
            error = error[:197] + "..."
            
        return f"✗ {workflow_name} Error: {error}"
    
    def _parse_html_error(self, html_content: str) -> str:
        """Extract error message from HTML response."""
        # Simple HTML error extraction
        if "<title>" in html_content.lower():
            try:
                start = html_content.lower().index("<title>") + 7
                end = html_content.lower().index("</title>")
                return html_content[start:end].strip()
            except ValueError:
                pass
        
        # Look for common error patterns
        if "error" in html_content.lower():
            lines = html_content.split("\n")
            for line in lines:
                if "error" in line.lower() and len(line.strip()) < 200:
                    return line.strip()
        
        return "Server returned HTML error page"
    
    def _make_request(self, url: str, data: Dict[str, Any]) -> Tuple[bool, Any]:
        """Make HTTP request with retry logic using urllib."""
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                # Prepare request
                json_data = json.dumps(data).encode('utf-8')
                req = Request(
                    url,
                    data=json_data,
                    headers={'Content-Type': 'application/json'},
                    method='POST'
                )
                
                # Make request with timeout
                with urlopen(req, timeout=self.timeout) as response:
                    status_code = response.getcode()
                    response_data = response.read().decode('utf-8')
                    
                    # Parse response
                    try:
                        result = json.loads(response_data)
                        return True, result
                    except json.JSONDecodeError:
                        # n8n might return plain text
                        return True, {"message": response_data}
                    
            except HTTPError as e:
                # HTTP error responses
                status_code = e.code
                
                if status_code == 404:
                    return False, "Webhook not found (404). Check webhook URL."
                elif status_code == 500:
                    return False, "Server error (500). Check n8n workflow configuration."
                else:
                    # Read error response body once and reuse it
                    try:
                        error_body = e.read().decode('utf-8')
                    except:
                        error_body = ""
                    
                    # Try to parse error message as JSON
                    try:
                        error_data = json.loads(error_body)
                        error_msg = error_data.get("message", error_data.get("error", f"HTTP {status_code}"))
                        return False, error_msg
                    except:
                        # Check if HTML error page
                        try:
                            if "<html" in error_body.lower() or "<!doctype" in error_body.lower():
                                error_msg = self._parse_html_error(error_body)
                                return False, error_msg
                            return False, f"HTTP {status_code}: {error_body[:100]}"
                        except:
                            return False, f"HTTP {status_code} error"
                    
            except URLError as e:
                # Network/connection errors
                if "timeout" in str(e).lower():
                    last_error = f"Request timeout after {self.timeout}s"
                else:
                    last_error = f"Connection failed: {str(e.reason)[:100]}"
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delays[attempt])
                    continue
            
            except Exception as e:
                last_error = f"Unexpected error: {str(e)[:100]}"
                break
        
        return False, last_error or "Request failed after retries"
    
    def execute(self, workflow_id: str, params: Dict[str, Any]) -> int:
        """
        Execute a workflow and print result to stdout.
        Returns 0 on success, 1 on error.
        """
        # Validate workflow exists in config
        workflow_config = self._get_workflow_config(workflow_id)
        if not workflow_config:
            print(self._format_error(workflow_id, f"Workflow '{workflow_id}' not found in config"))
            return 1
        
        # Build webhook URL
        webhook_url = self._build_webhook_url(workflow_id)
        if not webhook_url:
            print(self._format_error(workflow_id, "Invalid webhook configuration"))
            return 1
        
        # Execute request
        success, result = self._make_request(webhook_url, params)
        
        if success:
            print(self._format_success(workflow_id, result))
            
            # If there's structured data to return, print it on a separate line
            if isinstance(result, dict) and "data" in result:
                try:
                    print(json.dumps(result["data"], indent=2))
                except:
                    pass
            
            return 0
        else:
            print(self._format_error(workflow_id, result))
            return 1


def main():
    """Main entry point for CLI usage."""
    parser = argparse.ArgumentParser(
        description="Execute n8n workflows via webhooks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python bridge.py email_workflow --recipient "user@example.com" --template "welcome"
  python bridge.py notification_workflow --message "Hello World" --channel "general"
        """
    )
    
    parser.add_argument(
        "workflow_id",
        help="Workflow ID from config.json"
    )
    
    parser.add_argument(
        "--config",
        help="Path to config.json (default: ./config.json)",
        default=None
    )
    
    # All other arguments are passed as workflow parameters
    parser.add_argument(
        "--param",
        action="append",
        nargs=2,
        metavar=("KEY", "VALUE"),
        help="Workflow parameter (can be used multiple times)"
    )
    
    # Parse known args to allow dynamic parameters
    args, unknown = parser.parse_known_args()
    
    # Build parameters dictionary from --param arguments and unknown args
    params = {}
    
    if args.param:
        for key, value in args.param:
            params[key] = value
    
    # Parse unknown arguments as key=value or --key value pairs
    i = 0
    while i < len(unknown):
        arg = unknown[i]
        if arg.startswith("--"):
            key = arg[2:]
            if i + 1 < len(unknown) and not unknown[i + 1].startswith("--"):
                value = unknown[i + 1]
                i += 2
            else:
                value = "true"
                i += 1
            params[key] = value
        else:
            i += 1
    
    # Initialize bridge and execute
    try:
        bridge = N8NBridge(config_path=args.config)
        exit_code = bridge.execute(args.workflow_id, params)
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n✗ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Fatal Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

