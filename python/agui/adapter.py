"""
Adapter layer for mapping between Agent Zero and AG-UI protocol.

Handles message conversion, response mapping, tool calls, and state synchronization.
"""

import json
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from agent import UserMessage, AgentContext
from python.helpers.log import LogItem


@dataclass
class AGUIEvent:
    """AG-UI protocol event structure."""
    type: str
    context_id: str
    data: Dict[str, Any]
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            import time
            self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for transport."""
        return {
            "type": self.type,
            "context_id": self.context_id,
            "timestamp": self.timestamp,
            "data": self.data,
        }


class MessageAdapter:
    """Adapter for converting AG-UI messages to Agent Zero format."""
    
    @staticmethod
    def from_agui_message(event: Dict[str, Any]) -> UserMessage:
        """
        Convert AG-UI message event to UserMessage.
        
        AG-UI message format:
        {
            "type": "message",
            "data": {
                "text": "message text",
                "message_id": "optional-id",
                "attachments": ["path1", "path2"]
            }
        }
        """
        data = event.get("data", {})
        text = data.get("text", "")
        attachments = data.get("attachments", [])
        message_id = data.get("message_id")
        
        # Create UserMessage
        message = UserMessage(
            message=text,
            attachments=attachments or []
        )
        
        return message
    
    @staticmethod
    def extract_context_id(event: Dict[str, Any]) -> Optional[str]:
        """Extract context_id from AG-UI event."""
        return event.get("context_id") or event.get("data", {}).get("context_id")


class ResponseAdapter:
    """Adapter for converting Agent Zero responses to AG-UI events."""
    
    @staticmethod
    def log_item_to_event(log_item: LogItem, context_id: str) -> AGUIEvent:
        """Convert LogItem to AG-UI event."""
        log_type = log_item.type
        log_data = log_item.output()
        
        # Map log types to AG-UI event types
        event_type_map = {
            "user": "message",
            "response": "response",
            "agent": "agent_action",
            "error": "error",
            "tool": "tool_call",
            "tool_result": "tool_result",
        }
        
        event_type = event_type_map.get(log_type, "log_update")
        
        return AGUIEvent(
            type=event_type,
            context_id=context_id,
            data={
                "log_item": log_data,
                "message_id": log_data.get("id"),
                "content": log_data.get("content", ""),
                "heading": log_data.get("heading", ""),
                "temp": log_data.get("temp", False),
            }
        )
    
    @staticmethod
    def stream_chunk_to_event(
        chunk: str,
        full: str,
        context_id: str,
        message_id: Optional[str] = None
    ) -> AGUIEvent:
        """Convert stream chunk to AG-UI stream event."""
        return AGUIEvent(
            type="stream_chunk",
            context_id=context_id,
            data={
                "chunk": chunk,
                "full": full,
                "message_id": message_id,
            }
        )
    
    @staticmethod
    def stream_end_to_event(
        context_id: str,
        message_id: Optional[str] = None,
        final_text: Optional[str] = None
    ) -> AGUIEvent:
        """Convert stream end to AG-UI event."""
        return AGUIEvent(
            type="stream_end",
            context_id=context_id,
            data={
                "message_id": message_id,
                "final_text": final_text,
            }
        )
    
    @staticmethod
    def error_to_event(
        error: str,
        context_id: str,
        message_id: Optional[str] = None
    ) -> AGUIEvent:
        """Convert error to AG-UI event."""
        return AGUIEvent(
            type="error",
            context_id=context_id,
            data={
                "error": error,
                "message_id": message_id,
            }
        )
    
    @staticmethod
    def progress_to_event(
        progress: str,
        context_id: str,
        active: bool = False
    ) -> AGUIEvent:
        """Convert progress update to AG-UI event."""
        return AGUIEvent(
            type="progress",
            context_id=context_id,
            data={
                "progress": progress,
                "active": active,
            }
        )


class ToolAdapter:
    """Adapter for tool call events."""
    
    @staticmethod
    def tool_call_to_event(
        tool_name: str,
        tool_args: Dict[str, Any],
        context_id: str,
        call_id: Optional[str] = None
    ) -> AGUIEvent:
        """Convert tool call to AG-UI event."""
        import uuid
        return AGUIEvent(
            type="tool_call",
            context_id=context_id,
            data={
                "call_id": call_id or str(uuid.uuid4()),
                "tool_name": tool_name,
                "tool_args": tool_args,
            }
        )
    
    @staticmethod
    def tool_result_to_event(
        call_id: str,
        result: Any,
        context_id: str,
        error: Optional[str] = None
    ) -> AGUIEvent:
        """Convert tool result to AG-UI event."""
        return AGUIEvent(
            type="tool_result",
            context_id=context_id,
            data={
                "call_id": call_id,
                "result": result,
                "error": error,
            }
        )


class StateAdapter:
    """Adapter for state synchronization events."""
    
    @staticmethod
    def context_state_to_event(context: AgentContext) -> AGUIEvent:
        """Convert context state to AG-UI event."""
        context_output = context.output()
        return AGUIEvent(
            type="context_state",
            context_id=context.id,
            data={
                "context": context_output,
                "paused": context.paused,
                "log_guid": context.log.guid,
                "log_version": len(context.log.updates),
            }
        )
    
    @staticmethod
    def context_list_to_event(contexts: List[Dict[str, Any]]) -> AGUIEvent:
        """Convert context list to AG-UI event."""
        return AGUIEvent(
            type="context_list",
            context_id="",  # Global event
            data={
                "contexts": contexts,
            }
        )
    
    @staticmethod
    def notification_to_event(
        notification: Dict[str, Any],
        context_id: Optional[str] = None
    ) -> AGUIEvent:
        """Convert notification to AG-UI event."""
        return AGUIEvent(
            type="notification",
            context_id=context_id or "",
            data={
                "notification": notification,
            }
        )

