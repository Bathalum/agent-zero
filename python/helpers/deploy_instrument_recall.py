"""
Instrument Recall Deployment Helper

This script helps deploy the instrument recall extension to agent profiles.

Usage:
    python -m python.helpers.deploy_instrument_recall --profiles researcher,developer
    python -m python.helpers.deploy_instrument_recall --profiles researcher --rollback
    python -m python.helpers.deploy_instrument_recall --list

Features:
- Copy extension templates to specified profiles
- Create default instruments.json if needed
- Validate deployment
- Rollback capability
"""

import argparse
import os
import shutil
from pathlib import Path
from typing import List
from python.helpers import files


RECALL_TEMPLATE = "python/extensions/profiles/_55_recall_instruments_template.py"
WAIT_TEMPLATE = "python/extensions/profiles/_91_recall_instruments_wait_template.py"

DEFAULT_INSTRUMENTS_CONFIG = {
    "enabled": True,
    "recall_interval": 5,
    "max_instruments": 3,
    "similarity_threshold": 0.4,
    "auto_equip": [],
    "excluded": [],
    "filters": {
        "tags": [],
        "priority_max": None
    }
}


def list_profiles() -> List[str]:
    """List all available agent profiles."""
    agents_dir = files.get_abs_path("agents")
    
    if not os.path.exists(agents_dir):
        return []
    
    profiles = []
    for item in os.listdir(agents_dir):
        item_path = os.path.join(agents_dir, item)
        # Skip files and special directories
        if os.path.isdir(item_path) and not item.startswith("_"):
            profiles.append(item)
    
    return sorted(profiles)


def _print_safe(text: str):
    """Print text in a way that's safe for Windows console encoding."""
    try:
        print(text)
    except UnicodeEncodeError:
        # Fallback to ASCII if console doesn't support Unicode
        print(text.encode('ascii', 'replace').decode('ascii'))


def deploy_to_profile(profile: str, create_config: bool = True, backup: bool = True) -> bool:
    """
    Deploy instrument recall extensions to a specific profile.
    
    Args:
        profile: Profile name (e.g., "researcher", "developer")
        create_config: Whether to create default instruments.json if missing
        backup: Whether to backup existing files before overwriting
    
    Returns:
        True if successful, False otherwise
    """
    print(f"\n=== Deploying to profile: {profile} ===")
    
    # Validate profile exists
    profile_dir = files.get_abs_path("agents", profile)
    if not os.path.exists(profile_dir):
        print(f"[X] Error: Profile directory not found: {profile_dir}")
        return False
    
    # Create extensions directory if needed
    extensions_dir = os.path.join(profile_dir, "extensions", "message_loop_prompts_after")
    os.makedirs(extensions_dir, exist_ok=True)
    print(f"[+] Extensions directory ready: {extensions_dir}")
    
    # Paths for template files
    recall_template_path = files.get_abs_path(RECALL_TEMPLATE)
    wait_template_path = files.get_abs_path(WAIT_TEMPLATE)
    
    if not os.path.exists(recall_template_path):
        print(f"[X] Error: Recall template not found: {recall_template_path}")
        return False
    
    if not os.path.exists(wait_template_path):
        print(f"[X] Error: Wait template not found: {wait_template_path}")
        return False
    
    # Target paths
    recall_target = os.path.join(extensions_dir, "_55_recall_instruments.py")
    wait_target = os.path.join(extensions_dir, "_91_recall_instruments_wait.py")
    
    # Backup existing files if requested
    if backup:
        for target in [recall_target, wait_target]:
            if os.path.exists(target):
                backup_path = target + ".backup"
                shutil.copy2(target, backup_path)
                print(f"[+] Backed up: {os.path.basename(target)} -> {os.path.basename(backup_path)}")
    
    # Copy template files
    try:
        shutil.copy2(recall_template_path, recall_target)
        print(f"[+] Deployed: _55_recall_instruments.py")
        
        shutil.copy2(wait_template_path, wait_target)
        print(f"[+] Deployed: _91_recall_instruments_wait.py")
    except Exception as e:
        print(f"[X] Error copying files: {e}")
        return False
    
    # Create default instruments.json if requested and doesn't exist
    if create_config:
        config_path = os.path.join(profile_dir, "instruments.json")
        if not os.path.exists(config_path):
            import json
            try:
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(DEFAULT_INSTRUMENTS_CONFIG, f, indent=2)
                print(f"[+] Created: instruments.json (default config)")
            except Exception as e:
                print(f"[!] Warning: Could not create instruments.json: {e}")
        else:
            print(f"[+] Found existing: instruments.json")
    
    print(f"[SUCCESS] Successfully deployed to {profile}")
    return True


def rollback_profile(profile: str) -> bool:
    """
    Rollback deployment by restoring from backup files.
    
    Args:
        profile: Profile name
    
    Returns:
        True if successful, False otherwise
    """
    print(f"\n=== Rolling back profile: {profile} ===")
    
    profile_dir = files.get_abs_path("agents", profile)
    extensions_dir = os.path.join(profile_dir, "extensions", "message_loop_prompts_after")
    
    if not os.path.exists(extensions_dir):
        print(f"[X] Error: Extensions directory not found")
        return False
    
    recall_target = os.path.join(extensions_dir, "_55_recall_instruments.py")
    wait_target = os.path.join(extensions_dir, "_91_recall_instruments_wait.py")
    
    recall_backup = recall_target + ".backup"
    wait_backup = wait_target + ".backup"
    
    restored = False
    
    # Restore from backups
    for target, backup in [(recall_target, recall_backup), (wait_target, wait_backup)]:
        if os.path.exists(backup):
            try:
                shutil.copy2(backup, target)
                os.remove(backup)
                print(f"[+] Restored: {os.path.basename(target)}")
                restored = True
            except Exception as e:
                print(f"[X] Error restoring {os.path.basename(target)}: {e}")
        else:
            # No backup, so just remove the file
            if os.path.exists(target):
                try:
                    os.remove(target)
                    print(f"[+] Removed: {os.path.basename(target)}")
                    restored = True
                except Exception as e:
                    print(f"[X] Error removing {os.path.basename(target)}: {e}")
    
    if restored:
        print(f"[SUCCESS] Rollback complete for {profile}")
    else:
        print(f"[!] No changes to rollback for {profile}")
    
    return True


def validate_deployment(profile: str) -> bool:
    """
    Validate that the deployment was successful.
    
    Args:
        profile: Profile name
    
    Returns:
        True if valid, False otherwise
    """
    print(f"\n=== Validating deployment: {profile} ===")
    
    profile_dir = files.get_abs_path("agents", profile)
    extensions_dir = os.path.join(profile_dir, "extensions", "message_loop_prompts_after")
    
    recall_file = os.path.join(extensions_dir, "_55_recall_instruments.py")
    wait_file = os.path.join(extensions_dir, "_91_recall_instruments_wait.py")
    
    all_valid = True
    
    # Check files exist
    if not os.path.exists(recall_file):
        print(f"[X] Missing: _55_recall_instruments.py")
        all_valid = False
    else:
        print(f"[+] Found: _55_recall_instruments.py")
    
    if not os.path.exists(wait_file):
        print(f"[X] Missing: _91_recall_instruments_wait.py")
        all_valid = False
    else:
        print(f"[+] Found: _91_recall_instruments_wait.py")
    
    # Check instruments.json (optional but recommended)
    config_file = os.path.join(profile_dir, "instruments.json")
    if os.path.exists(config_file):
        print(f"[+] Found: instruments.json")
        
        # Try to parse it
        try:
            import json
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"  [+] Valid JSON structure")
        except Exception as e:
            print(f"  [X] Invalid JSON: {e}")
            all_valid = False
    else:
        print(f"[!] Missing: instruments.json (optional)")
    
    if all_valid:
        print(f"[SUCCESS] Deployment is valid")
    else:
        print(f"[ERROR] Deployment has issues")
    
    return all_valid


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Deploy instrument recall extension to agent profiles",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Deploy to specific profiles
  python -m python.helpers.deploy_instrument_recall --profiles researcher,developer
  
  # Deploy without creating config file
  python -m python.helpers.deploy_instrument_recall --profiles researcher --no-config
  
  # Rollback deployment
  python -m python.helpers.deploy_instrument_recall --profiles researcher --rollback
  
  # List available profiles
  python -m python.helpers.deploy_instrument_recall --list
  
  # Validate deployment
  python -m python.helpers.deploy_instrument_recall --profiles researcher --validate
        """
    )
    
    parser.add_argument(
        "--profiles",
        type=str,
        help="Comma-separated list of profiles to deploy to (e.g., researcher,developer)"
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available profiles"
    )
    
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="Rollback deployment (restore from backup)"
    )
    
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate deployment without making changes"
    )
    
    parser.add_argument(
        "--no-config",
        action="store_true",
        help="Don't create instruments.json if missing"
    )
    
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Don't backup existing files"
    )
    
    args = parser.parse_args()
    
    # List profiles
    if args.list:
        profiles = list_profiles()
        print("\nAvailable profiles:")
        for profile in profiles:
            print(f"  - {profile}")
        print(f"\nTotal: {len(profiles)} profiles")
        return
    
    # Validate profiles argument
    if not args.profiles:
        parser.error("--profiles is required (or use --list)")
        return
    
    # Parse profiles
    profiles = [p.strip() for p in args.profiles.split(",")]
    
    print(f"\n{'='*60}")
    print(f"Instrument Recall Extension Deployment")
    print(f"{'='*60}")
    print(f"Profiles: {', '.join(profiles)}")
    print(f"Action: {'Rollback' if args.rollback else 'Validate' if args.validate else 'Deploy'}")
    print(f"{'='*60}")
    
    # Process each profile
    results = {}
    for profile in profiles:
        if args.rollback:
            results[profile] = rollback_profile(profile)
        elif args.validate:
            results[profile] = validate_deployment(profile)
        else:
            results[profile] = deploy_to_profile(
                profile,
                create_config=not args.no_config,
                backup=not args.no_backup
            )
    
    # Summary
    print(f"\n{'='*60}")
    print("Summary:")
    print(f"{'='*60}")
    
    successful = [p for p, success in results.items() if success]
    failed = [p for p, success in results.items() if not success]
    
    if successful:
        print(f"[SUCCESS] Successful: {', '.join(successful)}")
    
    if failed:
        print(f"[ERROR] Failed: {', '.join(failed)}")
    
    print(f"\nTotal: {len(successful)}/{len(profiles)} successful")


if __name__ == "__main__":
    main()

