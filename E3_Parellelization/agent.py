import os, json, re 
import mlflow
from dotenv import load_dotenv
from google.adk.agents import LlmAgent, ParallelAgent, SequentialAgent, LoopAgent
from google.adk.tools import google_search
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.tool_context import ToolContext
from typing import Optional
from google.genai import types
from tools import calculator_tool, read_data_tool, list_example_files_tool, get_processing_status_tool, update_processing_status_tool, assign_file_for_work_tool, get_work_assignments_tool, complete_assignment_tool

# Import agent factory functions
from agents import (
    create_file_todo_list_agent,
    create_plan_and_assign_tasks_agent,
    create_read_summarize_files_agent,
    create_merger_agent,
    create_chunk_manager_agent,
    create_chunk_analyzer_agent,
)

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

load_dotenv()

# 1. Setup MLflow Experiment
mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"))
experiment_name = "E3_Parellelization_Traces"
experiment = mlflow.get_experiment_by_name(experiment_name)
if experiment is None:
    experiment_id = mlflow.create_experiment(experiment_name)
else:
    experiment_id = experiment.experiment_id

# 2. Configure the exporter
MLFLOW_SERVER_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")

otlp_exporter = OTLPSpanExporter(
    endpoint=f"{MLFLOW_SERVER_URI}/v1/traces",
    headers={
        "Content-Type": "application/x-protobuf",
        "x-mlflow-experiment-id": experiment_id,
    }
)

# 3. Configure the tracer provider
tracer_provider = TracerProvider()
tracer_provider.add_span_processor(SimpleSpanProcessor(otlp_exporter))
trace.set_tracer_provider(tracer_provider)


def check_for_pending_files(context: CallbackContext) -> bool:
    """
    Checks the todo_list_result in state for any tasks with status 'pending'.
    Returns True to continue the loop, False to stop the loop.
    """
    todo_list_raw = context.state.get("todo_list_result")
    
    if isinstance(todo_list_raw, str):
        try:
            todo_list = json.loads(todo_list_raw)
        except json.JSONDecodeError:
            print("Warning: todo_list_result is not valid JSON string.")
            return False 
    elif isinstance(todo_list_raw, list):
        todo_list = todo_list_raw
    else:
        return False

    has_pending = any(task.get("status") == "pending" for task in todo_list if isinstance(task, dict))
    return has_pending


# Create agents using factory functions
file_todo_list_agent = create_file_todo_list_agent()
plan_and_assign_tasks_agent = create_plan_and_assign_tasks_agent()
read_summarize_files_agent1 = create_read_summarize_files_agent(1)
read_summarize_files_agent2 = create_read_summarize_files_agent(2)
merger_agent = create_merger_agent()
chunk_manager_agent = create_chunk_manager_agent()
chunk_analyzer_agent = create_chunk_analyzer_agent()


# --- Create Composite Agents ---

# Parallel agent that runs both file summarization agents concurrently
parallel_agents_summarize = ParallelAgent(
    name="ParallelFileSummarizationAgent",
    sub_agents=[read_summarize_files_agent1, read_summarize_files_agent2],
    description="Runs multiple file summarization agents in parallel."
)

# Loop agent that repeatedly assigns and processes pending files
file_processing_loop = LoopAgent(
    name="FileProcessingLoop",
    sub_agents=[plan_and_assign_tasks_agent, parallel_agents_summarize],
    max_iterations=10,
    description="Repeatedly assigns and processes pending files until all are completed."
)

# Chunk analysis loop for document chunking and analysis
analysis_loop = LoopAgent(
    name="DocumentAnalysisLoop",
    sub_agents=[chunk_manager_agent, chunk_analyzer_agent],
    max_iterations=50,
    description="Iterates through document chunks to build a final summary."
)


# --- Create Main Sequential Pipeline ---
sequential_pipeline_agent = SequentialAgent(
    name="FileExtractionPipelineAgent",
    sub_agents=[
        file_todo_list_agent,    # 1. Initialize the todo list
        analysis_loop,    # 2. Process all files in a loop until none are pending
        merger_agent             # 3. Final synthesis of all results
    ],
    description="Coordinates file processing using a loop to ensure all files are handled and synthesizes the results."
)

root_agent = sequential_pipeline_agent