# Advanced Profile System Testing Guide

This document outlines comprehensive testing scenarios for the advanced profile management system.

## Test Scenarios

### 1. Create Custom Profile from Scratch

**Objective**: Verify blank profile creation works correctly.

**Steps**:
1. Navigate to Profile Manager
2. Click "Create New Profile"
3. Enter profile name: `test_custom`
4. Verify profile is created with default structure
5. Open profile editor
6. Verify all tabs are accessible
7. Verify basic metadata is set

**Expected Result**: Profile created successfully with all required files and folders.

---

### 2. Duplicate Built-in Profile

**Objective**: Verify duplication of built-in profiles.

**Steps**:
1. Navigate to Profile Manager
2. Select a built-in profile (e.g., `developer`)
3. Click "Duplicate" button
4. Enter new profile name: `test_dev_copy`
5. Verify new profile is created
6. Open editor and verify all prompts/extensions/tools were copied
7. Verify metadata shows `base_profile: developer`

**Expected Result**: All files copied correctly, custom profile is editable.

---

### 3. Edit All Prompt Types

**Objective**: Verify prompt editing functionality.

**Steps**:
1. Create or open a custom profile
2. Navigate to "Behavior" tab
3. Select "Role (Identity & Capabilities)" prompt
4. Switch to Markdown editor
5. Modify content and save
6. Switch to "Communication" prompt
7. Modify and save
8. Switch to "Environment" prompt
9. Modify and save
10. Reload profile and verify changes persisted

**Expected Result**: All prompt changes saved and loaded correctly.

---

### 4. Enable/Disable Extensions

**Objective**: Verify extension management.

**Steps**:
1. Open a custom profile
2. Navigate to "Extensions" tab
3. Click "Add Extension"
4. Enter path: `message_loop_prompts_after/_60_test_extension.py`
5. Verify extension appears in list
6. Click "View" to see content
7. Click "Edit" to modify
8. Click "Remove" to delete
9. Confirm removal

**Expected Result**: Extensions can be added, viewed, edited, and removed.

---

### 5. Add Custom Tools

**Objective**: Verify tool management.

**Steps**:
1. Open a custom profile
2. Navigate to "Tools" tab
3. Click "Add Tool"
4. Enter filename: `test_tool.py`
5. Verify tool appears in list
6. Click "View" to see content
7. Click "Edit" to modify
8. Click "Remove" to delete
9. Confirm removal

**Expected Result**: Tools can be added, viewed, edited, and removed.

---

### 6. Configure Instrument Settings

**Objective**: Verify instrument recall configuration.

**Steps**:
1. Open a custom profile
2. Navigate to "Configuration" tab
3. Enable "Instrument Recall"
4. Set recall interval: 3
5. Set max instruments: 5
6. Set similarity threshold: 0.5
7. Click "Save Configuration"
8. Reload profile and verify settings persisted

**Expected Result**: Configuration saves and loads correctly.

---

### 7. Switch Between Profiles

**Objective**: Verify profile switching works.

**Steps**:
1. Note current active profile
2. Select different profile
3. Click "Switch"
4. Confirm switch operation
5. Verify page reloads
6. Verify new profile is active
7. Verify agent behavior matches new profile

**Expected Result**: Profile switches successfully, agent uses new profile.

---

### 8. Delete Custom Profile

**Objective**: Verify profile deletion with safety checks.

**Steps**:
1. Create a test profile
2. Try to delete active profile (should fail)
3. Switch to different profile
4. Try to delete built-in profile (should fail)
5. Delete custom test profile
6. Confirm deletion
7. Verify profile is removed from list
8. Verify files are deleted from disk

**Expected Result**: Safety checks work, custom profiles can be deleted.

---

### 9. Import/Export Profile

**Objective**: Verify profile packaging.

**Steps**:
1. Create or select a custom profile
2. Click "Export" button
3. Verify ZIP file downloads
4. Extract ZIP and verify contents
5. Delete the profile
6. Click "Import Profile"
7. Select the ZIP file
8. Enter new profile name
9. Verify profile is imported
10. Open editor and verify all content is present

**Expected Result**: Profile exports as valid ZIP, imports successfully.

---

### 10. Validate Error Handling

**Objective**: Verify error handling and edge cases.

**Test Cases**:

#### 10.1 Invalid Profile Names
- Try creating profile with spaces: `test profile`
- Try creating profile with special chars: `test@profile`
- Try creating profile with existing name
- Expected: Proper error messages

#### 10.2 Built-in Protection
- Try editing built-in profile prompts (should be disabled)
- Try deleting built-in profile (should fail)
- Try adding extensions to built-in (should be disabled)
- Expected: Read-only mode enforced

#### 10.3 Missing Files
- Manually delete a prompt file
- Open profile editor
- Expected: Graceful handling, empty content shown

#### 10.4 Invalid JSON
- Manually corrupt instruments.json
- Open configuration tab
- Expected: Default config loaded, warning shown

#### 10.5 Profile Validation
- Create profile with missing _context.md
- Run validation
- Expected: Validation errors reported

---

## Integration Testing

### Profile Loading on Startup

**Test**: Verify profile loads correctly when agent starts.

**Steps**:
1. Set custom profile as active
2. Restart agent
3. Verify custom profile loaded
4. Check logs for errors
5. Verify prompts and extensions loaded

---

### Profile Fallback

**Test**: Verify fallback to agent0 when profile missing.

**Steps**:
1. Set active profile to custom profile
2. Manually delete the custom profile directory
3. Restart agent
4. Verify system falls back to `agent0`
5. Verify no crashes

---

### Instrument Recall Integration

**Test**: Verify instrument recall works with profile config.

**Steps**:
1. Create profile with instrument recall enabled
2. Configure recall_interval and thresholds
3. Assign instruments to profile
4. Switch to profile
5. Chat with agent
6. Verify instruments recalled according to config

---

## Performance Testing

### Large Profile Collections

**Test**: Verify system handles many profiles.

**Steps**:
1. Create 50+ custom profiles
2. Navigate to profile manager
3. Verify list loads quickly
4. Search/filter profiles
5. Switch between profiles

**Expected**: No significant slowdown.

---

### Large Prompt Files

**Test**: Verify handling of large prompt files.

**Steps**:
1. Create prompt with 10,000+ lines
2. Load in editor
3. Edit and save
4. Verify performance acceptable

---

## Security Testing

### Path Traversal Prevention

**Test**: Verify security against directory traversal.

**Steps**:
1. Try creating extension with path: `../../etc/passwd`
2. Try reading prompt: `../../../../sensitive.file`
3. Expected: Rejected with error

---

### Built-in Profile Protection

**Test**: Verify built-ins cannot be modified via API.

**Steps**:
1. Call API to modify developer profile
2. Expected: 400 error
3. Verify built-in files unchanged

---

## Regression Testing

Run after any changes to profile system:

1. Verify existing profiles still load
2. Verify agent initialization works
3. Verify profile switching doesn't break
4. Verify backward compatibility with old profile.json formats
5. Verify upstream updates don't break custom profiles

---

## Manual Testing Checklist

- [ ] Create blank profile
- [ ] Duplicate built-in profile
- [ ] Edit role prompt
- [ ] Edit communication prompt
- [ ] Edit environment prompt
- [ ] Add custom extension
- [ ] Remove extension
- [ ] Add custom tool
- [ ] Remove tool
- [ ] Assign instruments
- [ ] Unassign instruments
- [ ] Configure instrument recall
- [ ] Switch profiles
- [ ] Delete custom profile
- [ ] Export profile
- [ ] Import profile
- [ ] Validate profile
- [ ] Test with invalid names
- [ ] Test built-in protection
- [ ] Test error handling
- [ ] Test profile fallback
- [ ] Test on fresh installation

---

## Automated Testing (Future)

Future automated test suite should cover:

- Unit tests for all helper functions
- Integration tests for API endpoints
- End-to-end tests for UI workflows
- Performance benchmarks
- Security penetration testing

---

## Bug Reporting

When reporting bugs, include:

1. Profile ID and type (built-in/custom)
2. Steps to reproduce
3. Expected vs actual behavior
4. Error messages/logs
5. Browser console errors (for UI issues)
6. Profile metadata (profile.json contents)
7. System info (OS, Python version, etc.)








