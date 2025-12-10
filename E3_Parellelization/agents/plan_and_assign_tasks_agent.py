"""Plan and Assign Tasks Agent - assigns files to processing agents."""

from google.adk.agents import LlmAgent
from tools import read_data_tool, list_example_files_tool, get_processing_status_tool
from .utils import exit_loop


GEMINI_MODEL = "gemini-2.5-flash"


def create_plan_and_assign_tasks_agent():
    """Create and return the PlanAndAssignTasksAgent."""
    return LlmAgent(
        name="PlanAndAssignTasksAgent",
        model=GEMINI_MODEL,
        instruction="""You are an AI Task Planner Agent, you check what files are in the on the todo list:
    {todo_list_result}
    Then you assign tasks to each file in the todo list to a agent that will read and summarize the file. 
    Return an updated todo list with the assigned agent for each file.
    Avaialble agents are ReadSummarizeFilesAgent1 and ReadSummarizeFilesAgent2.

    If all files are already assigned and status is "completed", you MUST call the 'exit_loop' function. Do not output any text.
""",
        description="Plans and assigns tasks to processing agents.",
        tools=[read_data_tool, list_example_files_tool, get_processing_status_tool, exit_loop],
        output_key="todo_list_result"
    )
