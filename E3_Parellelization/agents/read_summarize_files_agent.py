"""Read and Summarize Files Agent - reads files and creates summaries."""

import time
import json
import re
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from tools import read_data_tool, list_example_files_tool, get_processing_status_tool


GEMINI_MODEL = "gemini-2.5-flash"


def update_structured_todo_callback_reusable(callback_context: CallbackContext):
    """Updates the specific task in the structured todo_list_result based on the agent's own name."""
    current_agent_name = callback_context.agent_name
    print(f"Callback triggered by: {current_agent_name}")
    
    todo_list_raw = callback_context.state.get("todo_list_result")
    todo_list = []
    
    if isinstance(todo_list_raw, str):
        match = re.search(r"```json\s*([\s\S]*?)\s*```", todo_list_raw)
        if match:
            json_content = match.group(1)
        else:
            json_content = todo_list_raw
        
        try:
            todo_list = json.loads(json_content)
        except json.JSONDecodeError:
            print("ERROR: Could not parse todo_list_result as JSON.")
            return None
            
    elif isinstance(todo_list_raw, list):
        todo_list = todo_list_raw
    else:
        print("Warning: todo_list_result is empty or unexpected type.")
        return None

    task_updated = False
    print(f"Callback: Current agent name is '{current_agent_name}'")
    
    for i, task in enumerate(todo_list):
        if isinstance(task, dict):
            assigned_agent = task.get("assigned_agent")
            print(f"Callback Debug: Task {i} Filename: {task.get('filename')}, Assigned: '{assigned_agent}', Status: {task.get('status')}")

            if assigned_agent == current_agent_name:
                task["status"] = "completed"
                task["processed_at"] = time.time()
                task_updated = True
                print(f"Callback: Marked task for {task.get('filename')} as completed.")
                break
    
    if task_updated:
        print("Callback SUCCESS: Saving updated todo list to state.")
        callback_context.state["todo_list_result"] = todo_list
    else:
        print("Callback FAILURE: No matching 'pending' task found for this agent. State not updated.")
        
    return None


def create_read_summarize_files_agent(agent_number: int):
    """Create and return a ReadSummarizeFilesAgent with a specific number."""
    agent_name = f"ReadSummarizeFilesAgent{agent_number}"
    output_key_str = f"ReadSummarizeFilesAgent{agent_number}_result"
    
    return LlmAgent(
        name=agent_name,
        model=GEMINI_MODEL,
        instruction="""You are a AI File Summarization Agent, you read the files in the example_data directory and create a summary based on the file contents.
    Todo List: {todo_list_result}
Use the Read Example Data tool to read the files in the example_data directory.
Output a concise summary of each file you read.
""",
        description="Summarizes files from example_data directory.",
        tools=[read_data_tool, list_example_files_tool, get_processing_status_tool],
        output_key=output_key_str,
        after_agent_callback=update_structured_todo_callback_reusable
    )
