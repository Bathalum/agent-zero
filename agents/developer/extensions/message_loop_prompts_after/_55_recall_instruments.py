"""
Instrument Recall Extension Template

This extension intelligently recalls relevant instruments from memory based on
agent profile, task context, and metadata tags.

To use this extension:
1. Copy to: agents/{profile}/extensions/message_loop_prompts_after/_55_recall_instruments.py
2. Create optional config: agents/{profile}/instruments.json
3. Enable in settings or per-profile config

Features:
- Profile-specific instrument filtering
- Similarity-based search
- Priority sorting
- Auto-equip instruments
- Exclusion lists
- Custom thresholds per profile
"""

import asyncio
import os
import json
from typing import Any
from python.helpers import log, settings, errors, files
from python.helpers.extension import Extension
from python.helpers.memory import Memory
from python.helpers.instrument_metadata import InstrumentMetadata
from agent import Agent, LoopData

DATA_NAME_TASK = "_recall_instruments_task"
DATA_NAME_ITER = "_recall_instruments_iter"


class RecallInstruments(Extension):
    """
    Extension to recall relevant instruments based on agent profile and context.
    
    This extension:
    - Runs at configured intervals (similar to memory recall)
    - Searches memory for instruments matching the agent's profile
    - Filters by enabled status and applies profile-specific rules
    - Sorts by priority and injects into agent prompt
    """
    
    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        set = settings.get_settings()
        
        # Load and apply profile-specific config
        profile_config = self._load_profile_config()
        set = self._apply_profile_config(set, profile_config)
        
        # Check if instrument recall is enabled (after profile override)
        if not set.get("instrument_recall_enabled", False):
            return
        
        # Check interval - recall every X iterations
        if loop_data.iteration % set.get("instrument_recall_interval", 5) != 0:
            return
        
        # Create log item to show progress
        log_item = self.agent.context.log.log(
            type="util",
            heading=f"Recalling instruments for profile '{self.agent.config.profile or 'default'}'",
        )
        
        # Start async task for instrument search
        task = asyncio.create_task(
            self.search_instruments(loop_data=loop_data, log_item=log_item, profile_config=profile_config, **kwargs)
        )
        
        # Store task and iteration for wait extension
        self.agent.set_data(DATA_NAME_TASK, task)
        self.agent.set_data(DATA_NAME_ITER, loop_data.iteration)
    
    async def search_instruments(self, log_item: log.LogItem, loop_data: LoopData, profile_config: dict, **kwargs):
        """
        Search memory for relevant instruments based on task context and profile.
        
        Algorithm:
        1. Build search query from user message + history
        2. Search memory with profile filter
        3. Apply profile-specific filters (auto-equip, exclusions)
        4. Sort by priority
        5. Format and inject into prompt
        """
        set = settings.get_settings()
        extras = loop_data.extras_persistent
        
        # Cleanup previous instruments from extras
        if "instruments" in extras:
            del extras["instruments"]
        
        # Get agent profile
        profile = self.agent.config.profile or "default"
        
        # Build search query from current task and context
        user_instruction = (
            loop_data.user_message.output_text() if loop_data.user_message else ""
        )
        history = self.agent.history.output_text()[-2000:]  # Last 2k chars of history
        
        query = f"Profile: {profile}\nTask: {user_instruction}\nContext: {history}"
        
        # Get memory database
        try:
            db = await Memory.get(self.agent)
        except Exception as e:
            log_item.update(heading=f"Error accessing memory: {str(e)}")
            return
        
        # Build filter for profile and enabled instruments
        # Filter format: "area == 'instruments' and enabled == True and (profile in profiles)"
        profile_filter = f"area == '{Memory.Area.INSTRUMENTS.value}' and enabled == True"
        profile_filter += f" and ('{profile}' in profiles or 'default' in profiles)"
        
        # Apply additional filters from profile config
        if profile_config.get("filters"):
            filters = profile_config["filters"]
            
            # Tag filters
            if filters.get("tags"):
                tag_conditions = " or ".join([f"'{tag}' in tags" for tag in filters["tags"]])
                profile_filter += f" and ({tag_conditions})"
            
            # Priority filter
            if filters.get("priority_max") is not None:
                profile_filter += f" and priority <= {filters['priority_max']}"
        
        # Search memory for relevant instruments
        try:
            instruments = await db.search_similarity_threshold(
                query=query,
                limit=set.get("instrument_recall_max_search", 8),
                threshold=set.get("instrument_recall_similarity_threshold", 0.4),
                filter=profile_filter,
            )
        except Exception as e:
            err = errors.format_error(e)
            log_item.update(heading=f"Error searching instruments: {err}")
            return
        
        # Handle auto-equip instruments (always include these)
        auto_equipped = []
        auto_equip_ids = profile_config.get("auto_equip", [])
        if auto_equip_ids:
            auto_equipped = await self._get_auto_equip_instruments(db, auto_equip_ids, profile)
        
        # Combine auto-equipped with search results
        all_instruments = auto_equipped + instruments
        
        # Remove duplicates (auto-equip takes precedence)
        seen_ids = set()
        unique_instruments = []
        for instr in all_instruments:
            instr_id = instr.metadata.get("instrument_id", "")
            if instr_id and instr_id not in seen_ids:
                seen_ids.add(instr_id)
                unique_instruments.append(instr)
        
        # Filter out excluded instruments
        excluded_ids = profile_config.get("excluded", [])
        if excluded_ids:
            unique_instruments = [
                instr for instr in unique_instruments
                if instr.metadata.get("instrument_id") not in excluded_ids
            ]
        
        if not unique_instruments:
            log_item.update(heading="No relevant instruments found")
            return
        
        # Sort by priority (lower number = higher priority)
        instruments_sorted = sorted(
            unique_instruments,
            key=lambda x: x.metadata.get("priority", 5)
        )
        
        # Limit to max results
        max_result = set.get("instrument_recall_max_result", 3)
        instruments_sorted = instruments_sorted[:max_result]
        
        # Update log with results
        log_item.update(
            heading=f"{len(instruments_sorted)} relevant instruments recalled",
        )
        
        # Format instruments for prompt
        instruments_txt = self._format_instruments(instruments_sorted)
        
        if instruments_txt:
            log_item.update(instruments=instruments_txt)
            
            # Inject into prompt using existing template
            extras["instruments"] = self.agent.parse_prompt(
                "agent.system.instruments.md",
                instruments=instruments_txt
            )
    
    async def _get_auto_equip_instruments(self, db: Memory, auto_equip_ids: list[str], profile: str) -> list:
        """
        Load auto-equip instruments from memory by ID.
        
        Args:
            db: Memory database instance
            auto_equip_ids: List of instrument IDs to auto-equip
            profile: Current agent profile
        
        Returns:
            List of Document objects for auto-equip instruments
        """
        auto_equipped = []
        
        # Load metadata to check enabled status
        registry = InstrumentMetadata.load_registry()
        
        for instrument_id in auto_equip_ids:
            # Check if instrument exists and is enabled
            instr_meta = registry.get("instruments", {}).get(instrument_id)
            if not instr_meta or not instr_meta.get("enabled", True):
                continue
            
            # Check if instrument is assigned to this profile
            profiles = instr_meta.get("profiles", ["default"])
            if profile not in profiles and "default" not in profiles:
                continue
            
            # Search for this specific instrument in memory
            try:
                filter_str = f"area == '{Memory.Area.INSTRUMENTS.value}' and instrument_id == '{instrument_id}'"
                results = await db.search_similarity_threshold(
                    query=instrument_id,  # Simple query, filter does the work
                    limit=1,
                    threshold=0.0,  # Low threshold since we're filtering by exact ID
                    filter=filter_str,
                )
                
                if results:
                    auto_equipped.extend(results)
            except Exception:
                # Skip this instrument if search fails
                continue
        
        return auto_equipped
    
    def _format_instruments(self, instruments: list) -> str:
        """
        Format instruments for display in agent prompt.
        
        Args:
            instruments: List of Document objects with instrument data
        
        Returns:
            Formatted string with instrument information
        """
        formatted = []
        for instr in instruments:
            name = instr.metadata.get("instrument_id", "Unknown")
            content = instr.page_content
            formatted.append(f"## {name}\n{content}")
        
        return "\n\n".join(formatted)
    
    def _load_profile_config(self) -> dict:
        """
        Load profile-specific instrument configuration.
        
        Looks for: agents/{profile}/instruments.json
        
        Returns:
            Dictionary with profile config or empty dict if not found
        """
        profile = self.agent.config.profile
        if not profile:
            return {}
        
        try:
            config_path = files.get_abs_path("agents", profile, "instruments.json")
            
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            # Silently fail and use defaults
            pass
        
        return {}
    
    def _apply_profile_config(self, global_settings: dict, profile_config: dict) -> dict:
        """
        Override global settings with profile-specific configuration.
        
        Args:
            global_settings: Settings from main config
            profile_config: Settings from profile's instruments.json
        
        Returns:
            Merged settings dictionary
        """
        if not profile_config:
            return global_settings
        
        # Create a copy to avoid modifying original
        settings_copy = global_settings.copy()
        
        # Override settings if profile specifies them
        if "enabled" in profile_config:
            settings_copy["instrument_recall_enabled"] = profile_config["enabled"]
        
        if "recall_interval" in profile_config:
            settings_copy["instrument_recall_interval"] = profile_config["recall_interval"]
        
        if "max_instruments" in profile_config:
            settings_copy["instrument_recall_max_result"] = profile_config["max_instruments"]
        
        if "similarity_threshold" in profile_config:
            settings_copy["instrument_recall_similarity_threshold"] = profile_config["similarity_threshold"]
        
        return settings_copy

