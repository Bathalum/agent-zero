"""
Instrument Migration Script

Migrates existing n8n instruments to the new metadata system.
This script:
1. Scans instruments/custom/n8n/workflows/ for existing .md files
2. Creates metadata entries with default values
3. Assigns to "default" profile
4. Preserves existing functionality
"""

import os
import json
from pathlib import Path
from python.helpers import files
from python.helpers.instrument_metadata import InstrumentMetadata


def migrate_existing_instruments(verbose: bool = True) -> dict:
    """
    Migrate existing n8n instruments to metadata registry.
    
    Args:
        verbose: If True, print progress messages
    
    Returns:
        Dictionary with migration results
    """
    results = {
        "success": True,
        "migrated": [],
        "skipped": [],
        "errors": []
    }
    
    try:
        # Get path to n8n workflows directory
        workflows_dir = files.get_abs_path("instruments/custom/n8n/workflows")
        
        if not os.path.exists(workflows_dir):
            if verbose:
                print("No n8n workflows directory found. Nothing to migrate.")
            return results
        
        # Load existing metadata registry
        registry = InstrumentMetadata.load_registry()
        existing_instruments = set(registry.get("instruments", {}).keys())
        
        # Scan for .md files
        workflow_files = []
        for file in os.listdir(workflows_dir):
            if file.endswith(".md"):
                workflow_files.append(file)
        
        if verbose:
            print(f"Found {len(workflow_files)} instrument file(s) to check")
        
        # Process each workflow file
        for workflow_file in workflow_files:
            workflow_name = workflow_file.replace(".md", "")
            instrument_id = f"n8n.{workflow_name}"
            
            # Skip if already in metadata registry
            if instrument_id in existing_instruments:
                results["skipped"].append(instrument_id)
                if verbose:
                    print(f"  ✓ {instrument_id} - already in registry")
                continue
            
            try:
                # Read workflow file to extract description
                file_path = os.path.join(workflows_dir, workflow_file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract description from first line after "# Problem"
                description = f"{workflow_name.replace('_', ' ').title()} workflow"
                lines = content.split("\n")
                for i, line in enumerate(lines):
                    if line.strip().startswith("# Problem"):
                        if i + 1 < len(lines):
                            desc_line = lines[i + 1].strip()
                            if desc_line:
                                description = desc_line
                        break
                
                # Create metadata entry
                InstrumentMetadata.set_instrument_metadata(
                    instrument_id=instrument_id,
                    metadata={
                        "type": "n8n",
                        "source_path": f"instruments/custom/n8n/workflows/{workflow_file}",
                        "profiles": ["default"],
                        "tags": ["n8n", "workflow"],
                        "priority": 5,
                        "enabled": True,
                        "metadata": {
                            "display_name": workflow_name.replace("_", " ").title(),
                            "category": "N8N Workflow",
                            "migrated": True
                        }
                    }
                )
                
                results["migrated"].append(instrument_id)
                if verbose:
                    print(f"  ✓ {instrument_id} - migrated successfully")
                    
            except Exception as e:
                error_msg = f"{instrument_id}: {str(e)}"
                results["errors"].append(error_msg)
                if verbose:
                    print(f"  ✗ {instrument_id} - error: {str(e)}")
        
        if verbose:
            print(f"\nMigration complete:")
            print(f"  - Migrated: {len(results['migrated'])}")
            print(f"  - Skipped: {len(results['skipped'])}")
            print(f"  - Errors: {len(results['errors'])}")
        
    except Exception as e:
        results["success"] = False
        results["errors"].append(f"Migration failed: {str(e)}")
        if verbose:
            print(f"Migration failed: {str(e)}")
    
    return results


def initialize_metadata_registry(force: bool = False, verbose: bool = True) -> bool:
    """
    Initialize the metadata registry file if it doesn't exist.
    
    Args:
        force: If True, overwrites existing registry
        verbose: If True, print progress messages
    
    Returns:
        True if initialized, False if already exists (and not forced)
    """
    registry_path = files.get_abs_path("instruments/metadata.json")
    
    if os.path.exists(registry_path) and not force:
        if verbose:
            print("Metadata registry already exists.")
        return False
    
    try:
        # Create initial registry structure
        initial_registry = {
            "version": "1.0",
            "instruments": {}
        }
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(registry_path), exist_ok=True)
        
        # Write initial registry
        with open(registry_path, 'w', encoding='utf-8') as f:
            json.dump(initial_registry, f, indent=2, ensure_ascii=False)
        
        if verbose:
            print(f"Initialized metadata registry at: {registry_path}")
        
        return True
        
    except Exception as e:
        if verbose:
            print(f"Failed to initialize metadata registry: {str(e)}")
        return False


def run_full_migration(verbose: bool = True) -> dict:
    """
    Run full migration process:
    1. Initialize metadata registry (if needed)
    2. Migrate existing instruments
    
    Args:
        verbose: If True, print progress messages
    
    Returns:
        Dictionary with migration results
    """
    if verbose:
        print("=" * 60)
        print("Instrument Metadata Migration")
        print("=" * 60)
        print()
    
    # Step 1: Initialize registry
    if verbose:
        print("Step 1: Initialize metadata registry")
    
    initialized = initialize_metadata_registry(force=False, verbose=verbose)
    
    if verbose:
        print()
    
    # Step 2: Migrate instruments
    if verbose:
        print("Step 2: Migrate existing instruments")
    
    results = migrate_existing_instruments(verbose=verbose)
    
    if verbose:
        print()
        print("=" * 60)
        print("Migration complete!")
        print("=" * 60)
    
    return results


if __name__ == "__main__":
    """Run migration when script is executed directly."""
    import sys
    
    verbose = "--quiet" not in sys.argv
    
    results = run_full_migration(verbose=verbose)
    
    # Exit with error code if migration failed
    sys.exit(0 if results["success"] else 1)

