#!/usr/bin/env python3
"""
N8N Workflow Testing Utility
Test workflows before embedding them into Agent Zero's memory.
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, Optional
import subprocess
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


class WorkflowTester:
    """Utility for testing n8n workflows."""
    
    def __init__(self, base_path: Optional[Path] = None):
        """Initialize tester."""
        if base_path is None:
            base_path = Path(__file__).parent
        self.base_path = base_path
        self.config_path = base_path / "config.json"
        self.bridge_path = base_path / "bridge.py"
        
    def load_config(self) -> dict:
        """Load configuration."""
        if not self.config_path.exists():
            print(f"Error: Config file not found: {self.config_path}")
            sys.exit(1)
            
        with open(self.config_path, 'r') as f:
            return json.load(f)
    
    def get_workflow_config(self, workflow_id: str) -> Optional[dict]:
        """Get configuration for a specific workflow."""
        config = self.load_config()
        return config.get("workflows", {}).get(workflow_id)
    
    def test_connectivity(self, workflow_id: str) -> tuple[bool, str]:
        """Test if the workflow webhook is reachable."""
        config = self.load_config()
        workflow_config = self.get_workflow_config(workflow_id)
        
        if not workflow_config:
            return False, f"Workflow '{workflow_id}' not found in config"
        
        base_url = config.get("n8n_base_url", "").rstrip("/")
        webhook_path = workflow_config.get("webhook_path", "").lstrip("/")
        webhook_url = f"{base_url}/{webhook_path}"
        
        print(f"Testing webhook: {webhook_url}")
        
        try:
            json_data = json.dumps({"test": True}).encode('utf-8')
            req = Request(
                webhook_url,
                data=json_data,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            
            with urlopen(req, timeout=10) as response:
                status_code = response.getcode()
                return True, f"Webhook is reachable (HTTP {status_code})"
                
        except HTTPError as e:
            if e.code == 404:
                return False, "Webhook not found (404)"
            elif e.code >= 500:
                return False, f"Server error ({e.code})"
            return True, f"Webhook is reachable (HTTP {e.code})"
            
        except URLError as e:
            if "timeout" in str(e).lower():
                return False, "Connection timeout (10s)"
            return False, f"Connection failed: {str(e.reason)[:100]}"
            
        except Exception as e:
            return False, f"Error: {str(e)[:100]}"
    
    def test_execution(self, workflow_id: str, params: Dict[str, Any]) -> tuple[bool, str]:
        """Test workflow execution using the bridge."""
        if not self.bridge_path.exists():
            return False, f"Bridge script not found: {self.bridge_path}"
        
        # Build command
        cmd = [sys.executable, str(self.bridge_path), workflow_id]
        for key, value in params.items():
            cmd.extend([f"--{key}", str(value)])
        
        print(f"Executing: {' '.join(cmd)}")
        print("-" * 60)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            print("-" * 60)
            
            if result.returncode == 0:
                return True, "Execution successful"
            else:
                return False, f"Execution failed (exit code {result.returncode})"
                
        except subprocess.TimeoutExpired:
            return False, "Execution timeout (60s)"
        except Exception as e:
            return False, f"Execution error: {str(e)}"
    
    def validate_config(self, workflow_id: str) -> tuple[bool, list[str]]:
        """Validate workflow configuration."""
        issues = []
        
        config = self.load_config()
        workflow_config = self.get_workflow_config(workflow_id)
        
        if not workflow_config:
            issues.append(f"Workflow '{workflow_id}' not found in config")
            return False, issues
        
        # Check required fields
        if not workflow_config.get("webhook_path"):
            issues.append("Missing 'webhook_path' in workflow config")
        
        if not workflow_config.get("description"):
            issues.append("Missing 'description' in workflow config")
        
        if not config.get("n8n_base_url"):
            issues.append("Missing 'n8n_base_url' in config")
        
        # Check instrument description exists
        workflows_dir = self.base_path / "workflows"
        description_path = workflows_dir / f"{workflow_id}.md"
        if not description_path.exists():
            issues.append(f"Instrument description not found: {description_path}")
        
        return len(issues) == 0, issues
    
    def run_full_test(self, workflow_id: str, params: Dict[str, Any]) -> bool:
        """Run complete test suite."""
        print(f"Testing workflow: {workflow_id}")
        print("=" * 60)
        
        all_passed = True
        
        # Test 1: Validate configuration
        print("\n1. Validating configuration...")
        valid, issues = self.validate_config(workflow_id)
        if valid:
            print("   ✓ Configuration is valid")
        else:
            print("   ✗ Configuration issues:")
            for issue in issues:
                print(f"     - {issue}")
            all_passed = False
        
        # Test 2: Check connectivity
        print("\n2. Testing webhook connectivity...")
        success, message = self.test_connectivity(workflow_id)
        if success:
            print(f"   ✓ {message}")
        else:
            print(f"   ✗ {message}")
            all_passed = False
        
        # Test 3: Execute workflow
        print("\n3. Testing workflow execution...")
        success, message = self.test_execution(workflow_id, params)
        if success:
            print(f"   ✓ {message}")
        else:
            print(f"   ✗ {message}")
            all_passed = False
        
        # Summary
        print("\n" + "=" * 60)
        if all_passed:
            print("✓ All tests passed!")
            print("\nWorkflow is ready to use. Restart Agent Zero to embed it.")
        else:
            print("✗ Some tests failed. Fix the issues before using this workflow.")
        
        return all_passed


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test n8n workflows before using with Agent Zero",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test connectivity only
  python test_workflow.py email_workflow --connectivity-only

  # Test with parameters
  python test_workflow.py email_workflow \\
    --recipient "test@example.com" \\
    --template "welcome"

  # Validate config only
  python test_workflow.py email_workflow --validate-only
        """
    )
    
    parser.add_argument(
        "workflow_id",
        help="Workflow ID to test"
    )
    
    parser.add_argument(
        "--connectivity-only",
        action="store_true",
        help="Only test webhook connectivity"
    )
    
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate configuration"
    )
    
    # Parse known args to allow dynamic parameters
    args, unknown = parser.parse_known_args()
    
    # Build parameters from unknown args
    params = {}
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
    
    # Initialize tester
    tester = WorkflowTester()
    
    try:
        if args.validate_only:
            # Validate only
            valid, issues = tester.validate_config(args.workflow_id)
            if valid:
                print("✓ Configuration is valid")
                sys.exit(0)
            else:
                print("✗ Configuration issues:")
                for issue in issues:
                    print(f"  - {issue}")
                sys.exit(1)
                
        elif args.connectivity_only:
            # Test connectivity only
            success, message = tester.test_connectivity(args.workflow_id)
            print(f"{'✓' if success else '✗'} {message}")
            sys.exit(0 if success else 1)
            
        else:
            # Run full test
            success = tester.run_full_test(args.workflow_id, params)
            sys.exit(0 if success else 1)
            
    except KeyboardInterrupt:
        print("\n\nTest cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

