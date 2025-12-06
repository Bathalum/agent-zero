# Profile UI Test Plan

## Scenarios

1. View all profiles
- Open Settings → Profiles tab
- Expect profile grid to render with avatars, names, and stats

2. Switch between profiles
- Use Quick Switcher in left panel
- Select a different profile; expect success toast and reload

3. Edit profile metadata
- Open a profile in the manager → Edit
- Change display name, description, category; Save
- Reopen to verify persistence

4. Change avatar icon/color
- Select icon and color; Save
- Verify quick switcher and manager show updated avatar

5. Assign/unassign instruments
- Toggle instruments in editor; Save
- Verify updated count in manager and retrieval via `/api/profile_instruments`

6. Quick switcher functionality
- Indicator shows current profile avatar and name
- Dropdown lists all profiles with active checkmark

7. Profile persistence after reload
- Reload page; current profile and metadata should persist

8. Multiple concurrent users
- Change profile on one client; verify others switch after reload

## Edge Cases
- No `profile.json` present: defaults used; no errors
- Missing `_context.md`: description fallback applied
- Invalid instrument id: server returns 404; UI handles gracefully
- Non-existent profile on switch: server 404 handled

## APIs to Verify
- POST `/api/profile_list`
- POST `/api/profile_metadata_get`
- POST `/api/profile_metadata_set`
- POST `/api/profile_switch`
- POST `/api/profile_instruments`

## Manual Checks
- Dark/light mode contrast for new components
- Responsive layout for manager and switcher
- Keyboard navigation focus states

