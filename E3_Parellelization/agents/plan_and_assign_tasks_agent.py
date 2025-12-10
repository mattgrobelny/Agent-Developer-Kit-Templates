"""Plan and Assign Tasks Agent - assigns files to processing agents."""

from google.adk.agents import LlmAgent
from tools import read_data_tool, list_example_files_tool, get_processing_status_tool
from .utils import exit_loop


GEMINI_MODEL = "gemini-2.5-flash"


def create_plan_and_assign_tasks_agent(num_agents: int = 2):
    """
    Create and return the PlanAndAssignTasksAgent.
    
    Args:
        num_agents: Number of available DocumentAnalyzer agents for load balancing
    """
    # Generate list of available agents dynamically - now using DocumentAnalyzer naming
    available_agents = [f"DocumentAnalyzer{i}" for i in range(1, num_agents + 1)]
    agents_list = ", ".join(available_agents)
    
    return LlmAgent(
        name="PlanAndAssignTasksAgent",
        model=GEMINI_MODEL,
        instruction=f"""You are an AI Task Planner Agent responsible for load balancing work across multiple processing agents.

Your task:
1. Check the todo list: {{todo_list_result}}
2. Assign each pending file to one of the available agents using round-robin load balancing
3. Ensure files are distributed evenly across agents

Available agents ({num_agents} total): {agents_list}

Load balancing strategy:
- Cycle through agents in order: DocumentAnalyzer1 → DocumentAnalyzer2 → ... → DocumentAnalyzer{num_agents} → DocumentAnalyzer1 (repeat)
- This ensures even distribution of work

Return an updated todo list with the "assigned_agent" field set for each file.

If all files are already assigned and status is "completed", you MUST call the 'exit_loop' function. Do not output any text.
""",
        description="Plans and assigns tasks to DocumentAnalyzer agents with load balancing.",
        tools=[read_data_tool, list_example_files_tool, get_processing_status_tool, exit_loop],
        output_key="todo_list_result"
    )
