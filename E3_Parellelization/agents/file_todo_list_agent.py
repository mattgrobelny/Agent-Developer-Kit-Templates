"""File Todo List Agent - creates a todo list of files in example_data directory."""

from google.adk.agents import LlmAgent
from ..tools import read_data_tool, list_example_files_tool, get_processing_status_tool

GEMINI_MODEL = "gemini-2.5-flash"


def create_file_todo_list_agent():
    """Create and return the FileTodoListAgent."""
    return LlmAgent(
        name="FileTodoListAgent",
        model=GEMINI_MODEL,
        instruction="""You are an AI File Todo List Agent, you check what files are in the example_data directory and create a todo list based on the file names.
Use the Read Example Data tool to list the files in the example_data directory.
Todo List format out as json: filename | moddt  | status  | processed_at | assigned_agent
""",
        description="Creates a todo list of files from example_data directory.",
        tools=[read_data_tool, list_example_files_tool, get_processing_status_tool],
        output_key="todo_list_result"
    )
