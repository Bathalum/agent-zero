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
        # Ensure error is a string and not empty
        error_str = str(error) if error else "Unknown error occurred"
        if not error_str.strip():
            error_str = "Unknown error occurred"
        
        # #region agent log
        import json
        import os
        from python.helpers import files
        try:
            DEBUG_LOG_PATH = files.get_abs_path(".cursor", "debug.log")
            os.makedirs(os.path.dirname(DEBUG_LOG_PATH), exist_ok=True)
            log_entry = {
                "location": "adapter.py:error_to_event",
                "message": "Creating error event",
                "timestamp": int(__import__("time").time() * 1000),
                "sessionId": "debug-session",
                "runId": "post-fix",
                "hypothesisId": "F",
                "data": {
                    "error_str": error_str,
                    "context_id": context_id,
                    "message_id": message_id,
                    "error_input": str(error) if error else None
                }
            }
            log_line = json.dumps(log_entry) + "\n"
            with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(log_line)
        except Exception as e:
            import sys
            print(f"[DEBUG LOG ERROR] {e}", file=sys.stderr)
        # #endregion
        
        event = AGUIEvent(
            type="error",
            context_id=context_id,
            data={
                "error": error_str,
                "message_id": message_id,
            }
        )
        
        # #region agent log
        try:
            DEBUG_LOG_PATH = files.get_abs_path(".cursor", "debug.log")
            os.makedirs(os.path.dirname(DEBUG_LOG_PATH), exist_ok=True)
            event_dict = event.to_dict()
            event_data = event_dict.get("data", {})
            log_entry = {
                "location": "adapter.py:error_to_event",
                "message": "Error event created",
                "timestamp": int(__import__("time").time() * 1000),
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "A",
                "data": {
                    "event_dict": event_dict,
                    "event_data": event_data,
                    "event_data_keys": list(event_data.keys()) if event_data else [],
                    "error_value": event_data.get("error", "MISSING"),
                    "error_value_type": type(event_data.get("error", None)).__name__ if event_data.get("error") else "None",
                    "error_value_length": len(str(event_data.get("error", ""))) if event_data.get("error") else 0,
                    "has_error_field": "error" in event_data,
                    "message_id_value": event_data.get("message_id"),
                    "full_event_json": json.dumps(event_dict)
                }
            }
            log_line = json.dumps(log_entry) + "\n"
            with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(log_line)
        except Exception as e:
            import sys
            print(f"[DEBUG LOG ERROR] {e}", file=sys.stderr)
        # #endregion
        
        return event
    
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

