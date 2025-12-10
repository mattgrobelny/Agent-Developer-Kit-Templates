# Adding a New Agent

This guide explains how to add a new agent to the E3_Parallelization project.

## File Structure

Agents are organized in the `agents/` directory:
```
agents/
  ├── __init__.py                      # Exports all agent factory functions
  ├── file_todo_list_agent.py          # Example: todo list agent
  ├── plan_and_assign_tasks_agent.py   # Example: task planning agent
  ├── read_summarize_files_agent.py    # Example: file summarization agent
  ├── synthesis_agent.py               # Example: synthesis agent
  └── chunk_agents.py                  # Example: multiple related agents
```

## Steps to Add a New Agent

### 1. Create a New Agent File

Create a new Python file in the `agents/` directory (e.g., `my_new_agent.py`):

```python
"""Description of what your agent does."""

from google.adk.agents import LlmAgent

GEMINI_MODEL = "gemini-2.5-flash"


def create_my_new_agent():
    """Create and return MyNewAgent."""
    return LlmAgent(
        name="MyNewAgent",
        model=GEMINI_MODEL,
        instruction="""You are a specialized AI agent.
Your task is to [describe what the agent does].
Use the tools provided to accomplish your goal.
Output [describe what output format is expected].
""",
        description="Brief description of the agent's purpose.",
        tools=[tool1, tool2, tool3],  # Add relevant tools
        output_key="my_new_agent_result"  # State key for storing results
    )
```

### 2. Export the Factory Function

Update `agents/__init__.py` to export your new agent factory function:

```python
"""Agents module - provides factory functions for all agents."""

from .file_todo_list_agent import create_file_todo_list_agent
from .plan_and_assign_tasks_agent import create_plan_and_assign_tasks_agent
from .read_summarize_files_agent import create_read_summarize_files_agent
from .synthesis_agent import create_merger_agent
from .chunk_agents import create_chunk_manager_agent, create_chunk_analyzer_agent
from .my_new_agent import create_my_new_agent  # Add this line

__all__ = [
    "create_file_todo_list_agent",
    "create_plan_and_assign_tasks_agent",
    "create_read_summarize_files_agent",
    "create_merger_agent",
    "create_chunk_manager_agent",
    "create_chunk_analyzer_agent",
    "create_my_new_agent",  # Add this line
]
```

### 3. Use the Agent in agent.py

Import and instantiate your agent in the main `agent.py` file:

```python
# At the top with other imports
from agents import (
    create_file_todo_list_agent,
    create_plan_and_assign_tasks_agent,
    create_read_summarize_files_agent,
    create_merger_agent,
    create_chunk_manager_agent,
    create_chunk_analyzer_agent,
    create_my_new_agent,  # Add this line
)

# Create your agent instance
my_new_agent = create_my_new_agent()

# Incorporate into your pipeline (ParallelAgent, SequentialAgent, LoopAgent, etc.)
```

## Key Components

### Agent Parameters

- **name** (str): Unique identifier for the agent (used in callbacks, state, and logging)
- **model** (str): The LLM model to use (e.g., "gemini-2.5-flash")
- **instruction** (str): System prompt describing the agent's task and behavior
- **description** (str): Human-readable description of the agent's purpose
- **tools** (list): List of available tools the agent can use
- **output_key** (str): State key where the agent's output is stored
- **after_agent_callback** (function, optional): Callback executed after the agent completes

### Accessing Tools

Available tools in the project:
- `read_data_tool` - Read files from example_data
- `list_example_files_tool` - List all files in example_data
- `get_processing_status_tool` - Check file processing status
- `update_processing_status_tool` - Update file processing status
- `assign_file_for_work_tool` - Assign work to agents
- `get_work_assignments_tool` - View current assignments
- `complete_assignment_tool` - Mark assignments as complete
- `calculator_tool` - Basic arithmetic
- `google_search` - Search the web

### State and Context

Agents share state through the agent framework:
- Access state: `{variable_name}` in instructions (uses state substitution)
- Write state: `output_key="my_result"` stores agent output for other agents
- Callbacks: Use `after_agent_callback` for custom state manipulation after execution

## Example: A Data Validator Agent

Here's a practical example of adding a validation agent:

**File: `agents/data_validator_agent.py`**
```python
"""Data Validator Agent - validates processed files."""

from google.adk.agents import LlmAgent

GEMINI_MODEL = "gemini-2.5-flash"


def create_data_validator_agent():
    """Create and return the DataValidatorAgent."""
    return LlmAgent(
        name="DataValidatorAgent",
        model=GEMINI_MODEL,
        instruction="""You are a data quality validation agent.
Review the following processed results: {synthesized_report}

Check for:
1. Completeness - all files were processed
2. Quality - summaries are coherent and comprehensive
3. Accuracy - no contradictions or errors
4. Format - output follows required structure

Output a validation report with findings and recommendations.
""",
        description="Validates processed data and reports quality metrics.",
        tools=[list_example_files_tool, get_processing_status_tool],
        output_key="validation_report"
    )
```

Then update `agents/__init__.py` and use it in your pipeline.

## Best Practices

1. **Naming**: Use descriptive names that indicate the agent's function
2. **Documentation**: Include docstrings in factory functions
3. **Tools**: Only include tools the agent needs (reduces confusion)
4. **Instructions**: Be specific about expected output format
5. **State Keys**: Use descriptive, unique output_key names
6. **Error Handling**: Reference tools that handle errors gracefully
7. **Testing**: Test agents individually before integrating into pipelines

## Troubleshooting

- **Agent not found**: Ensure it's exported in `agents/__init__.py`
- **State variables not populating**: Check `output_key` naming matches what you reference in other agents
- **Tool not available**: Verify it's in the agent's `tools` list
- **Callbacks not triggering**: Ensure callback function signature matches expected CallbackContext type
