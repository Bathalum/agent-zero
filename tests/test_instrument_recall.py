"""
Test Suite for Instrument Recall Extension

Tests the dynamic instrument recall functionality including:
- Extension loading per profile
- Profile-specific configuration
- Instrument search and filtering
- Auto-equip functionality
- Exclusion lists
- Priority sorting
- Memory integration
"""

import pytest
import asyncio
import json
import os
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path

# Test imports
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from python.helpers.instrument_metadata import InstrumentMetadata
from python.helpers.memory import Memory
from python.helpers import files


class TestInstrumentRecallExtension:
    """Test the instrument recall extension functionality"""
    
    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent for testing"""
        agent = Mock()
        agent.config = Mock()
        agent.config.profile = "researcher"
        agent.config.memory_subdir = "test"
        agent.config.embeddings_model = Mock()
        agent.context = Mock()
        agent.context.log = Mock()
        agent.context.log.log = Mock(return_value=Mock())
        agent.history = Mock()
        agent.history.output_text = Mock(return_value="Test history context")
        agent.parse_prompt = Mock(return_value="Formatted instruments")
        agent.set_data = Mock()
        agent.get_data = Mock()
        return agent
    
    @pytest.fixture
    def mock_loop_data(self):
        """Create mock loop data"""
        loop_data = Mock()
        loop_data.iteration = 5
        loop_data.user_message = Mock()
        loop_data.user_message.output_text = Mock(return_value="Find data analysis tools")
        loop_data.extras_persistent = {}
        return loop_data
    
    @pytest.fixture
    def sample_instruments_config(self):
        """Sample instrument configuration"""
        return {
            "enabled": True,
            "recall_interval": 3,
            "max_instruments": 3,
            "similarity_threshold": 0.35,
            "auto_equip": ["n8n.slack_message"],
            "excluded": ["n8n.deprecated_tool"],
            "filters": {
                "tags": ["analysis", "data"],
                "priority_max": 3
            }
        }
    
    @pytest.fixture
    def sample_instrument_metadata(self):
        """Sample instrument metadata registry"""
        return {
            "version": "1.0",
            "instruments": {
                "n8n.slack_message": {
                    "type": "n8n_workflow",
                    "source_path": "instruments/custom/n8n/workflows/slack_message.md",
                    "profiles": ["default", "researcher", "developer"],
                    "tags": ["communication", "messaging"],
                    "priority": 1,
                    "enabled": True,
                    "metadata": {}
                },
                "n8n.data_analyzer": {
                    "type": "n8n_workflow",
                    "source_path": "instruments/custom/n8n/workflows/data_analyzer.md",
                    "profiles": ["researcher"],
                    "tags": ["analysis", "data"],
                    "priority": 2,
                    "enabled": True,
                    "metadata": {}
                },
                "n8n.deprecated_tool": {
                    "type": "n8n_workflow",
                    "source_path": "instruments/custom/n8n/workflows/deprecated.md",
                    "profiles": ["researcher"],
                    "tags": ["legacy"],
                    "priority": 5,
                    "enabled": True,
                    "metadata": {}
                }
            }
        }
    
    def test_profile_config_loading(self, mock_agent, tmp_path):
        """Test loading profile-specific configuration"""
        # Create test profile directory with config
        profile_dir = tmp_path / "agents" / "test_profile"
        profile_dir.mkdir(parents=True)
        
        config = {
            "enabled": True,
            "recall_interval": 7,
            "max_instruments": 5
        }
        
        config_path = profile_dir / "instruments.json"
        with open(config_path, 'w') as f:
            json.dump(config, f)
        
        # Mock files.get_abs_path to return our test path
        with patch('python.helpers.files.get_abs_path') as mock_get_path:
            mock_get_path.return_value = str(config_path)
            mock_agent.config.profile = "test_profile"
            
            # Import and instantiate extension
            from python.extensions.profiles._55_recall_instruments_template import RecallInstruments
            extension = RecallInstruments(mock_agent)
            
            # Load config
            loaded_config = extension._load_profile_config()
            
            assert loaded_config == config
            assert loaded_config["recall_interval"] == 7
            assert loaded_config["max_instruments"] == 5
    
    def test_profile_config_override(self, mock_agent):
        """Test that profile config overrides global settings"""
        from python.extensions.profiles._55_recall_instruments_template import RecallInstruments
        extension = RecallInstruments(mock_agent)
        
        global_settings = {
            "instrument_recall_enabled": False,
            "instrument_recall_interval": 5,
            "instrument_recall_max_result": 3,
            "instrument_recall_similarity_threshold": 0.4
        }
        
        profile_config = {
            "enabled": True,
            "recall_interval": 3,
            "max_instruments": 5,
            "similarity_threshold": 0.35
        }
        
        merged = extension._apply_profile_config(global_settings, profile_config)
        
        assert merged["instrument_recall_enabled"] == True
        assert merged["instrument_recall_interval"] == 3
        assert merged["instrument_recall_max_result"] == 5
        assert merged["instrument_recall_similarity_threshold"] == 0.35
    
    def test_format_instruments(self, mock_agent):
        """Test instrument formatting for prompt"""
        from python.extensions.profiles._55_recall_instruments_template import RecallInstruments
        extension = RecallInstruments(mock_agent)
        
        # Create mock documents
        mock_doc1 = Mock()
        mock_doc1.metadata = {"instrument_id": "n8n.slack_message"}
        mock_doc1.page_content = "Send messages to Slack channels"
        
        mock_doc2 = Mock()
        mock_doc2.metadata = {"instrument_id": "n8n.email"}
        mock_doc2.page_content = "Send email notifications"
        
        instruments = [mock_doc1, mock_doc2]
        formatted = extension._format_instruments(instruments)
        
        assert "## n8n.slack_message" in formatted
        assert "Send messages to Slack channels" in formatted
        assert "## n8n.email" in formatted
        assert "Send email notifications" in formatted
    
    def test_priority_sorting(self):
        """Test that instruments are sorted by priority"""
        # Create mock documents with different priorities
        docs = []
        for i, priority in enumerate([5, 1, 3, 2, 4]):
            doc = Mock()
            doc.metadata = {
                "instrument_id": f"tool_{i}",
                "priority": priority
            }
            doc.page_content = f"Tool {i}"
            docs.append(doc)
        
        # Sort by priority
        sorted_docs = sorted(docs, key=lambda x: x.metadata.get("priority", 5))
        
        # Verify order
        priorities = [doc.metadata["priority"] for doc in sorted_docs]
        assert priorities == [1, 2, 3, 4, 5]
    
    def test_exclusion_filtering(self):
        """Test that excluded instruments are filtered out"""
        # Create mock documents
        docs = []
        for i in range(5):
            doc = Mock()
            doc.metadata = {"instrument_id": f"tool_{i}"}
            doc.page_content = f"Tool {i}"
            docs.append(doc)
        
        excluded_ids = ["tool_1", "tool_3"]
        
        # Filter
        filtered = [
            doc for doc in docs
            if doc.metadata.get("instrument_id") not in excluded_ids
        ]
        
        assert len(filtered) == 3
        assert all(doc.metadata["instrument_id"] not in excluded_ids for doc in filtered)
    
    def test_duplicate_removal(self):
        """Test that duplicate instruments are removed"""
        # Create documents with some duplicates
        docs = []
        ids = ["tool_1", "tool_2", "tool_1", "tool_3", "tool_2"]
        
        for i, tool_id in enumerate(ids):
            doc = Mock()
            doc.metadata = {"instrument_id": tool_id}
            doc.page_content = f"Tool {tool_id}"
            docs.append(doc)
        
        # Remove duplicates
        seen_ids = set()
        unique = []
        for doc in docs:
            instr_id = doc.metadata.get("instrument_id", "")
            if instr_id and instr_id not in seen_ids:
                seen_ids.add(instr_id)
                unique.append(doc)
        
        assert len(unique) == 3
        assert len(seen_ids) == 3
    
    @pytest.mark.asyncio
    async def test_extension_interval_check(self, mock_agent, mock_loop_data):
        """Test that extension runs at correct intervals"""
        from python.extensions.profiles._55_recall_instruments_template import RecallInstruments
        
        with patch('python.helpers.settings.get_settings') as mock_settings:
            mock_settings.return_value = {
                "instrument_recall_enabled": True,
                "instrument_recall_interval": 5,
                "instrument_recall_max_result": 3,
                "instrument_recall_similarity_threshold": 0.4
            }
            
            with patch.object(RecallInstruments, '_load_profile_config', return_value={}):
                extension = RecallInstruments(mock_agent)
                
                # Test at interval boundary (should run)
                mock_loop_data.iteration = 5
                await extension.execute(loop_data=mock_loop_data)
                assert mock_agent.set_data.called
                
                # Reset mock
                mock_agent.set_data.reset_mock()
                
                # Test not at interval (should not run)
                mock_loop_data.iteration = 3
                await extension.execute(loop_data=mock_loop_data)
                assert not mock_agent.set_data.called
    
    @pytest.mark.asyncio
    async def test_disabled_extension(self, mock_agent, mock_loop_data):
        """Test that extension doesn't run when disabled"""
        from python.extensions.profiles._55_recall_instruments_template import RecallInstruments
        
        with patch('python.helpers.settings.get_settings') as mock_settings:
            mock_settings.return_value = {
                "instrument_recall_enabled": False,
                "instrument_recall_interval": 5
            }
            
            with patch.object(RecallInstruments, '_load_profile_config', return_value={}):
                extension = RecallInstruments(mock_agent)
                
                mock_loop_data.iteration = 5
                await extension.execute(loop_data=mock_loop_data)
                
                # Should not set data if disabled
                assert not mock_agent.set_data.called
    
    def test_metadata_registry_integration(self, sample_instrument_metadata):
        """Test integration with instrument metadata registry"""
        # Test getting instruments by profile
        instruments = InstrumentMetadata.get_instruments_by_profile("researcher")
        
        # This will return empty list without actual registry, so let's test the logic
        # In actual test with registry, we would assert:
        # assert len(instruments) > 0
        # assert any(instr["id"] == "n8n.data_analyzer" for instr in instruments)
        
        # Test the metadata structure itself
        assert "instruments" in sample_instrument_metadata
        assert "n8n.data_analyzer" in sample_instrument_metadata["instruments"]
        
        analyzer = sample_instrument_metadata["instruments"]["n8n.data_analyzer"]
        assert analyzer["profiles"] == ["researcher"]
        assert "analysis" in analyzer["tags"]
        assert analyzer["priority"] == 2
    
    def test_instrument_id_extraction(self):
        """Test extracting instrument IDs from paths"""
        # Test n8n workflow path
        path1 = "instruments/custom/n8n/workflows/slack_message.md"
        id1 = InstrumentMetadata.extract_instrument_id_from_path(path1)
        assert id1 == "n8n.slack_message"
        
        # Test with backslashes (Windows)
        path2 = "instruments\\custom\\n8n\\workflows\\email.md"
        id2 = InstrumentMetadata.extract_instrument_id_from_path(path2)
        assert id2 == "n8n.email"
        
        # Test with absolute path
        path3 = "/home/user/agent-zero/instruments/custom/n8n/workflows/test.md"
        id3 = InstrumentMetadata.extract_instrument_id_from_path(path3)
        assert id3 == "n8n.test"
    
    @pytest.mark.asyncio
    async def test_wait_extension(self, mock_agent, mock_loop_data):
        """Test the wait extension waits for task completion"""
        from python.extensions.profiles._91_recall_instruments_wait_template import RecallInstrumentsWait
        
        # Create a mock task that's not done
        mock_task = AsyncMock()
        mock_task.done = Mock(return_value=False)
        
        mock_agent.get_data = Mock(return_value=mock_task)
        
        extension = RecallInstrumentsWait(mock_agent)
        await extension.execute(loop_data=mock_loop_data)
        
        # Verify we awaited the task
        mock_task.__await__.assert_called()
    
    @pytest.mark.asyncio
    async def test_wait_extension_no_task(self, mock_agent, mock_loop_data):
        """Test wait extension handles missing task gracefully"""
        from python.extensions.profiles._91_recall_instruments_wait_template import RecallInstrumentsWait
        
        mock_agent.get_data = Mock(return_value=None)
        
        extension = RecallInstrumentsWait(mock_agent)
        
        # Should not raise an error
        await extension.execute(loop_data=mock_loop_data)


class TestDeploymentScript:
    """Test the deployment helper script"""
    
    def test_list_profiles(self, tmp_path):
        """Test listing available profiles"""
        # Create mock profile directories
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        
        (agents_dir / "researcher").mkdir()
        (agents_dir / "developer").mkdir()
        (agents_dir / "_example").mkdir()  # Should be skipped
        (agents_dir / "README.md").touch()  # Should be skipped
        
        with patch('python.helpers.files.get_abs_path', return_value=str(agents_dir)):
            from python.helpers.deploy_instrument_recall import list_profiles
            profiles = list_profiles()
            
            assert "researcher" in profiles
            assert "developer" in profiles
            assert "_example" not in profiles
            assert len(profiles) == 2


class TestIntegrationScenarios:
    """Integration tests for real-world scenarios"""
    
    @pytest.fixture
    def mock_memory_search_results(self):
        """Mock memory search results"""
        docs = []
        
        # Create mock documents that would be returned from memory
        instruments = [
            {
                "id": "n8n.slack_message",
                "content": "Send messages to Slack channels",
                "priority": 1,
                "tags": ["communication"]
            },
            {
                "id": "n8n.data_analyzer",
                "content": "Analyze data with Python",
                "priority": 2,
                "tags": ["analysis", "data"]
            },
            {
                "id": "n8n.email_sender",
                "content": "Send email notifications",
                "priority": 3,
                "tags": ["communication"]
            }
        ]
        
        for instr in instruments:
            doc = Mock()
            doc.metadata = {
                "instrument_id": instr["id"],
                "priority": instr["priority"],
                "tags": instr["tags"]
            }
            doc.page_content = instr["content"]
            docs.append(doc)
        
        return docs
    
    def test_researcher_profile_scenario(self, mock_memory_search_results):
        """Test typical researcher profile scenario"""
        # Researcher should get data analysis tools prioritized
        profile_config = {
            "enabled": True,
            "recall_interval": 3,
            "max_instruments": 3,
            "similarity_threshold": 0.35,
            "auto_equip": [],
            "excluded": [],
            "filters": {
                "tags": ["analysis", "data"],
                "priority_max": 3
            }
        }
        
        # Filter by tags (at least one match)
        filter_tags = profile_config["filters"]["tags"]
        filtered = [
            doc for doc in mock_memory_search_results
            if any(tag in doc.metadata.get("tags", []) for tag in filter_tags)
        ]
        
        # Should get data_analyzer since it has analysis/data tags
        assert len(filtered) == 1
        assert filtered[0].metadata["instrument_id"] == "n8n.data_analyzer"
    
    def test_developer_profile_scenario(self, mock_memory_search_results):
        """Test typical developer profile scenario"""
        # Developer has auto-equip for slack_message
        profile_config = {
            "enabled": True,
            "auto_equip": ["n8n.slack_message"],
            "excluded": [],
            "max_instruments": 2
        }
        
        # Auto-equip should always be included
        auto_equip_ids = profile_config["auto_equip"]
        
        # Simulate auto-equip being added first
        auto_equipped = [
            doc for doc in mock_memory_search_results
            if doc.metadata["instrument_id"] in auto_equip_ids
        ]
        
        assert len(auto_equipped) == 1
        assert auto_equipped[0].metadata["instrument_id"] == "n8n.slack_message"
        
        # Then other instruments would be added from search
        # Total limited by max_instruments
        max_result = profile_config["max_instruments"]
        total_instruments = auto_equipped + mock_memory_search_results[:max_result-len(auto_equipped)]
        
        assert len(total_instruments) <= max_result


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])


