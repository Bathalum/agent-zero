# Advanced Profile Management User Guide

This guide helps you create, customize, and manage agent profiles in Agent Zero.

## Table of Contents

1. [Understanding Profiles](#understanding-profiles)
2. [Built-in vs Custom Profiles](#built-in-vs-custom-profiles)
3. [Creating Your First Custom Profile](#creating-your-first-custom-profile)
4. [Customizing Agent Behavior](#customizing-agent-behavior)
5. [Managing Extensions and Tools](#managing-extensions-and-tools)
6. [Configuring Skills](#configuring-skills)
7. [Import and Export](#import-and-export)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

---

## Understanding Profiles

**Agent profiles** define how your AI agent behaves, what skills it has access to, and how it communicates. Think of profiles as different "modes" or "personalities" for your agent.

Each profile contains:
- **System Prompts**: Define the agent's role, communication style, and behavior
- **Extensions**: Python code that extends the agent's capabilities
- **Tools**: Custom functions the agent can use
- **Skills**: Instruments (external integrations) assigned to the profile
- **Configuration**: Settings like instrument recall behavior

---

## Built-in vs Custom Profiles

### Built-in Profiles

Agent Zero comes with several pre-configured profiles:

- **agent0**: Default general-purpose agent
- **developer**: Specialized for software development
- **researcher**: Optimized for research and analysis
- **hacker**: Security and penetration testing focus

**Key points about built-in profiles:**
- ✅ Always available
- ✅ Updated with Agent Zero releases
- ❌ Cannot be edited directly in UI (read-only)
- ✅ Can be duplicated to create custom versions

### Custom Profiles

Custom profiles are user-created and fully editable:

- ✅ Full control over all aspects
- ✅ Can be based on built-in profiles
- ✅ Portable (export/import)
- ✅ Can be deleted when no longer needed

---

## Creating Your First Custom Profile

### Method 1: Create from Scratch

1. Navigate to **Settings → Profiles**
2. Click **"Create New Profile"**
3. Enter a profile name (e.g., `my_assistant`)
   - Use lowercase letters, numbers, underscores, or hyphens
   - No spaces or special characters
4. Click **Create**

The system will:
- Create the profile directory structure
- Generate default prompt files
- Set up basic configuration

### Method 2: Duplicate Built-in Profile

1. Navigate to **Settings → Profiles**
2. Find a built-in profile you like (e.g., `developer`)
3. Click the **"Duplicate"** button
4. Enter a new profile name (e.g., `my_developer`)
5. Click **Create**

This copies:
- All prompts
- All extensions
- All tools
- All configuration

You can then customize the copy without affecting the original.

---

## Customizing Agent Behavior

Agent behavior is defined by **system prompts**. There are three main prompt types:

### 1. Role Prompt (Identity & Capabilities)

Defines **who** the agent is and **what** it can do.

**Example structure:**
```markdown
# Agent Role

You are a helpful software development assistant specialized in web technologies.

## Core Capabilities
- Write and review code in JavaScript, Python, and React
- Debug issues and suggest fixes
- Explain technical concepts clearly

## Approach
- Always ask clarifying questions before starting
- Write clean, well-documented code
- Consider best practices and security
```

**To edit:**
1. Open profile editor
2. Go to **"Behavior"** tab
3. Select **"Role (Identity & Capabilities)"**
4. Edit in Markdown editor
5. Click **"Save Prompt"**

### 2. Communication Prompt (Style & Format)

Defines **how** the agent communicates.

**Example structure:**
```markdown
# Communication Style

## Response Format
- Be concise but thorough
- Use bullet points for lists
- Include code examples when relevant

## Thinking Process
- Show your reasoning
- Break down complex problems
- Explain your approach

## Tool Usage
- Use tools proactively
- Explain what each tool does
- Show results clearly
```

### 3. Environment Prompt (Context & Constraints)

Defines the **environment** the agent operates in.

**Example structure:**
```markdown
# Environment

## System Information
- Operating System: [Detected automatically]
- Available tools: code_execution, web_search, file_operations

## Constraints
- Cannot access external network directly
- Must use tools for file operations
- Always respect user privacy
```

---

## Managing Extensions and Tools

### Understanding Extensions

**Extensions** are Python hooks that modify agent behavior at specific points in the execution flow.

Common extension types:
- `message_loop_prompts_after`: Add dynamic prompts before LLM call
- `tool_execute_before`: Pre-process tool calls
- `response_stream`: Modify streaming responses

### Adding Extensions

1. Open profile editor
2. Go to **"Extensions"** tab
3. Click **"Add Extension"**
4. Enter path: `message_loop_prompts_after/_60_my_extension.py`
5. Edit the Python code
6. Save

**Simple extension example:**
```python
from python.helpers.extension import Extension

class MyExtension(Extension):
    async def execute(self, **kwargs):
        agent = kwargs.get("agent")
        # Your extension logic here
        return ""
```

### Managing Custom Tools

**Tools** are functions the agent can call during conversations.

### Adding a Tool

1. Open profile editor
2. Go to **"Tools"** tab
3. Click **"Add Tool"**
4. Enter filename: `my_tool.py`
5. Write tool code
6. Save

**Simple tool example:**
```python
from python.helpers.tool import Tool

class MyTool(Tool):
    async def execute(self, **kwargs):
        """
        Description of what this tool does.
        The agent will see this description.
        """
        # Tool implementation
        return "Tool result"
```

---

## Configuring Skills

### Assigning Instruments

**Instruments** are external integrations (Slack, email, APIs, etc.).

To assign instruments to a profile:

1. Open profile editor
2. Go to **"Skills"** tab
3. Toggle instruments on/off using switches
4. Assigned instruments will be available to the agent

### Instrument Recall Configuration

**Instrument recall** automatically equips relevant instruments based on conversation context.

To configure:

1. Go to **"Configuration"** tab
2. Enable **"Instrument Recall"**
3. Set parameters:
   - **Recall Interval**: How often to check (in messages)
   - **Max Instruments**: Maximum to equip at once
   - **Similarity Threshold**: Minimum relevance score (0.0-1.0)
4. Click **"Save Configuration"**

**Example configuration:**
```json
{
  "enabled": true,
  "recall_interval": 5,
  "max_instruments": 3,
  "similarity_threshold": 0.4
}
```

---

## Import and Export

### Exporting a Profile

Share your custom profile or back it up:

1. Navigate to profile manager
2. Find your custom profile
3. Click the **download icon**
4. Save the ZIP file

The ZIP contains:
- All prompt files
- Extensions
- Tools
- Configuration
- Metadata

### Importing a Profile

Use a profile shared by someone else:

1. Navigate to profile manager
2. Click **"Import Profile"**
3. Select the ZIP file
4. Enter a name for the imported profile
5. Click **Import**

The system will:
- Validate the profile structure
- Check for conflicts
- Import all files
- Report any warnings

---

## Best Practices

### Profile Organization

✅ **DO:**
- Use descriptive profile names (`web_developer`, `data_analyst`)
- Document your customizations in prompts
- Start from built-in profiles when possible
- Export profiles regularly as backups

❌ **DON'T:**
- Use special characters in profile names
- Modify built-in profiles (duplicate instead)
- Create too many similar profiles (consolidate)
- Delete profiles without backing up

### Prompt Writing

✅ **DO:**
- Be specific about agent capabilities
- Include examples in prompts
- Test changes incrementally
- Keep prompts focused and clear

❌ **DON'T:**
- Make prompts overly long (agent may miss details)
- Contradict yourself in different prompts
- Include sensitive information in prompts
- Use vague or ambiguous language

### Extension Development

✅ **DO:**
- Test extensions thoroughly
- Handle errors gracefully
- Document what each extension does
- Keep extensions focused on one task

❌ **DON'T:**
- Block the agent's execution flow
- Ignore error handling
- Modify agent state carelessly
- Create dependencies between extensions

---

## Troubleshooting

### Profile Won't Switch

**Symptom**: Clicking "Switch" doesn't change the profile.

**Solutions:**
1. Check browser console for errors
2. Verify profile exists in filesystem
3. Try refreshing the page
4. Check for validation errors

### Prompts Not Taking Effect

**Symptom**: Agent behavior doesn't match your prompts.

**Solutions:**
1. Verify you saved the prompt file
2. Restart the agent (reload page)
3. Check for syntax errors in prompts
4. Ensure you're editing the active profile

### Extension Doesn't Load

**Symptom**: Custom extension not executing.

**Solutions:**
1. Check Python syntax
2. Verify file path is correct
3. Check agent logs for errors
4. Ensure extension inherits from `Extension` class

### Profile Import Fails

**Symptom**: Error when importing profile ZIP.

**Solutions:**
1. Verify ZIP file is valid
2. Check for conflicting profile name
3. Ensure ZIP structure matches requirements
4. Review validation errors in error message

### Can't Delete Profile

**Symptom**: Delete button disabled or fails.

**Reasons:**
- Profile is currently active (switch first)
- Profile is built-in (cannot delete)
- Permission issues on filesystem

**Solution**: Switch to another profile, then try deleting.

---

## Getting Help

If you encounter issues not covered here:

1. **Check Logs**: Look in `agent-zero-data/logs/` for errors
2. **Validate Profile**: Use the validation feature in profile editor
3. **Community**: Ask in Agent Zero discussions/issues
4. **Reset**: As last resort, switch back to `agent0` (default)

---

## Example Workflows

### Creating a Data Science Profile

1. Duplicate `researcher` profile → `data_scientist`
2. Edit Role prompt:
   - Add Python/pandas/numpy expertise
   - Emphasize data visualization
   - Include statistical analysis skills
3. Assign instruments:
   - Enable database connectors
   - Enable visualization tools
4. Configure instrument recall:
   - `recall_interval: 3`
   - `similarity_threshold: 0.5`
5. Test with data analysis tasks

### Creating a Customer Support Profile

1. Create new profile → `support_agent`
2. Edit Communication prompt:
   - Friendly, empathetic tone
   - Clear explanations
   - Step-by-step guidance
3. Edit Role prompt:
   - Focus on helping users
   - Troubleshooting skills
   - Product knowledge
4. Assign instruments:
   - Ticket system integration
   - Knowledge base access
5. Add custom tool for common responses
6. Test with support scenarios

---

## Next Steps

- Explore built-in profiles to understand different configurations
- Experiment with different prompt styles
- Join the community to share custom profiles
- Read developer documentation for advanced customization

Happy profiling! 🚀
