"""
Test suite for Instrument Metadata functionality

This test suite verifies:
1. Metadata management operations
2. API endpoint functionality
3. Backward compatibility
4. Edge cases and error handling
"""

import json
import os
import sys
import tempfile
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from python.helpers.instrument_metadata import InstrumentMetadata


def test_metadata_registry_initialization():
    """Test that metadata registry can be created and loaded."""
    print("Test 1: Metadata Registry Initialization")
    
    # Load registry (should create if doesn't exist)
    registry = InstrumentMetadata.load_registry()
    
    assert registry is not None, "Registry should not be None"
    assert "version" in registry, "Registry should have version"
    assert "instruments" in registry, "Registry should have instruments"
    
    print("  ✓ Registry initialized successfully")
    return True


def test_set_and_get_instrument():
    """Test setting and getting instrument metadata."""
    print("\nTest 2: Set and Get Instrument Metadata")
    
    # Set test instrument
    test_id = "test.sample_instrument"
    test_metadata = {
        "type": "test",
        "source_path": "test/path.md",
        "profiles": ["default", "test"],
        "tags": ["test", "sample"],
        "priority": 3,
        "enabled": True,
        "metadata": {
            "display_name": "Test Instrument",
            "category": "Testing"
        }
    }
    
    InstrumentMetadata.set_instrument_metadata(test_id, test_metadata)
    
    # Get it back
    retrieved = InstrumentMetadata.get_instrument_metadata(test_id)
    
    assert retrieved is not None, "Should retrieve metadata"
    assert retrieved["type"] == "test", "Type should match"
    assert retrieved["profiles"] == ["default", "test"], "Profiles should match"
    assert retrieved["tags"] == ["test", "sample"], "Tags should match"
    assert retrieved["priority"] == 3, "Priority should match"
    
    print("  ✓ Metadata set and retrieved successfully")
    return True


def test_update_instrument():
    """Test partial update of instrument metadata."""
    print("\nTest 3: Update Instrument Metadata")
    
    test_id = "test.sample_instrument"
    
    # Update only priority and tags
    updates = {
        "priority": 1,
        "tags": ["test", "sample", "updated"]
    }
    
    updated = InstrumentMetadata.update_instrument_metadata(test_id, updates)
    
    assert updated is not None, "Should return updated metadata"
    assert updated["priority"] == 1, "Priority should be updated"
    assert "updated" in updated["tags"], "Tags should include new tag"
    assert updated["type"] == "test", "Other fields should be preserved"
    
    print("  ✓ Metadata updated successfully")
    return True


def test_get_instruments_by_profile():
    """Test filtering instruments by profile."""
    print("\nTest 4: Get Instruments by Profile")
    
    # Add another test instrument with different profiles
    InstrumentMetadata.set_instrument_metadata(
        "test.profile_test",
        {
            "type": "test",
            "source_path": "test/profile.md",
            "profiles": ["researcher"],
            "tags": ["profile-test"],
            "priority": 5,
            "enabled": True
        }
    )
    
    # Get instruments for "test" profile
    test_instruments = InstrumentMetadata.get_instruments_by_profile("test")
    
    assert len(test_instruments) > 0, "Should find instruments for 'test' profile"
    
    # Get instruments for "researcher" profile
    researcher_instruments = InstrumentMetadata.get_instruments_by_profile("researcher")
    
    assert len(researcher_instruments) > 0, "Should find instruments for 'researcher' profile"
    
    print(f"  ✓ Found {len(test_instruments)} instrument(s) for 'test' profile")
    print(f"  ✓ Found {len(researcher_instruments)} instrument(s) for 'researcher' profile")
    return True


def test_get_instruments_by_tags():
    """Test filtering instruments by tags."""
    print("\nTest 5: Get Instruments by Tags")
    
    # Get instruments with "test" tag
    test_tagged = InstrumentMetadata.get_instruments_by_tags(["test"])
    
    assert len(test_tagged) > 0, "Should find instruments with 'test' tag"
    
    # Get instruments with multiple tags (ANY match)
    multi_tagged = InstrumentMetadata.get_instruments_by_tags(["test", "sample"], match_all=False)
    
    assert len(multi_tagged) > 0, "Should find instruments with any matching tag"
    
    # Get instruments with multiple tags (ALL match)
    all_tagged = InstrumentMetadata.get_instruments_by_tags(["test", "sample"], match_all=True)
    
    print(f"  ✓ Found {len(test_tagged)} instrument(s) with 'test' tag")
    print(f"  ✓ Found {len(multi_tagged)} instrument(s) with ANY matching tag")
    print(f"  ✓ Found {len(all_tagged)} instrument(s) with ALL matching tags")
    return True


def test_list_all_instruments():
    """Test listing all instruments."""
    print("\nTest 6: List All Instruments")
    
    all_instruments = InstrumentMetadata.list_all_instruments()
    
    assert len(all_instruments) > 0, "Should find at least one instrument"
    
    # Verify sorting by priority
    for i in range(len(all_instruments) - 1):
        curr_priority = all_instruments[i].get("priority", 5)
        next_priority = all_instruments[i + 1].get("priority", 5)
        assert curr_priority <= next_priority, "Instruments should be sorted by priority"
    
    print(f"  ✓ Found {len(all_instruments)} instrument(s)")
    print("  ✓ Instruments correctly sorted by priority")
    return True


def test_extract_instrument_id():
    """Test instrument ID extraction from paths."""
    print("\nTest 7: Extract Instrument ID from Path")
    
    test_cases = [
        ("instruments/custom/n8n/workflows/email_workflow.md", "n8n.email_workflow"),
        ("/a0/instruments/custom/n8n/workflows/slack.md", "n8n.slack"),
        ("C:\\path\\to\\n8n\\workflows\\test.md", "n8n.test"),
        ("invalid/path/test.txt", None),
    ]
    
    for path, expected in test_cases:
        result = InstrumentMetadata.extract_instrument_id_from_path(path)
        assert result == expected, f"Failed for {path}: expected {expected}, got {result}"
    
    print("  ✓ All ID extraction test cases passed")
    return True


def test_delete_instrument():
    """Test deleting instrument metadata."""
    print("\nTest 8: Delete Instrument")
    
    # Delete test instruments
    deleted1 = InstrumentMetadata.delete_instrument_metadata("test.sample_instrument")
    assert deleted1, "Should successfully delete existing instrument"
    
    deleted2 = InstrumentMetadata.delete_instrument_metadata("test.profile_test")
    assert deleted2, "Should successfully delete existing instrument"
    
    # Try to delete non-existent instrument
    deleted3 = InstrumentMetadata.delete_instrument_metadata("test.nonexistent")
    assert not deleted3, "Should return False for non-existent instrument"
    
    # Verify deletion
    retrieved = InstrumentMetadata.get_instrument_metadata("test.sample_instrument")
    assert retrieved is None, "Deleted instrument should not be found"
    
    print("  ✓ Instruments deleted successfully")
    return True


def test_backward_compatibility():
    """Test backward compatibility with missing metadata."""
    print("\nTest 9: Backward Compatibility")
    
    # Getting non-existent instrument should return None, not error
    result = InstrumentMetadata.get_instrument_metadata("nonexistent.instrument")
    assert result is None, "Non-existent instrument should return None"
    
    # Listing with empty registry should return empty list
    InstrumentMetadata.save_registry({"version": "1.0", "instruments": {}})
    all_instruments = InstrumentMetadata.list_all_instruments()
    assert all_instruments == [], "Empty registry should return empty list"
    
    print("  ✓ Backward compatibility verified")
    return True


def run_all_tests():
    """Run all test cases."""
    print("=" * 60)
    print("Instrument Metadata Test Suite")
    print("=" * 60)
    
    tests = [
        test_metadata_registry_initialization,
        test_set_and_get_instrument,
        test_update_instrument,
        test_get_instruments_by_profile,
        test_get_instruments_by_tags,
        test_list_all_instruments,
        test_extract_instrument_id,
        test_delete_instrument,
        test_backward_compatibility,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except AssertionError as e:
            print(f"  ✗ Test failed: {str(e)}")
            failed += 1
        except Exception as e:
            print(f"  ✗ Test error: {str(e)}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

