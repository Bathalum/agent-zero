"""
Instrument Recall Wait Extension Template

This extension waits for the instrument recall task to complete before
proceeding with the agent's main LLM call.

To use this extension:
1. Copy to: agents/{profile}/extensions/message_loop_prompts_after/_91_recall_instruments_wait.py
2. Must be used in conjunction with _55_recall_instruments.py

The numbering (_91) ensures this runs after the recall extension (_55) but
before the main LLM call.
"""

from python.helpers.extension import Extension
from agent import LoopData

# Import task names from recall extension
DATA_NAME_TASK = "_recall_instruments_task"
DATA_NAME_ITER = "_recall_instruments_iter"


class RecallInstrumentsWait(Extension):
    """
    Wait for instrument recall task to complete.
    
    This ensures that the instrument recall search finishes before
    the agent proceeds with its main response generation.
    """
    
    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        """
        Wait for the instrument recall task if it exists and is not done.
        """
        task = self.agent.get_data(DATA_NAME_TASK)
        
        if task and not task.done():
            # Wait for task to complete
            await task

