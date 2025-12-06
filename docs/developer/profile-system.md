# Profile System

## Architecture Overview
- Backend file-backed metadata in `agents/<profile>/profile.json`
- Discovery via `_context.md` for descriptions
- Instrument assignments stored in instrument metadata mapped to profiles

## API Endpoints
- POST `/api/profile_list` → list profiles with enriched metadata
- POST `/api/profile_metadata_get` → read `profile.json` or defaults
- POST `/api/profile_metadata_set` → merge and save `profile.json`
- POST `/api/profile_switch` → set `settings.agent_profile`
- POST `/api/profile_instruments` → list/assign/unassign instruments

## State Management
- `webui/components/profiles/profile-store.js` centralizes profile state and API calls

## Components
- `profiles/profile-manager.html` main manager UI
- `profiles/profile-editor.html` modal editor
- `profiles/profile-switcher.html` quick switcher

## Styling
- `webui/css/profiles.css` styles for manager, editor, and switcher

## Extension Points
- Additional avatar icons via icon font classes
- Profile creation wizard (future) writing new `agents/<id>/profile.json`

## Notes
- All features degrade gracefully when `profile.json` is absent
- `_55_recall_instruments.py` presence is detected per profile for Smart Recall indicator

