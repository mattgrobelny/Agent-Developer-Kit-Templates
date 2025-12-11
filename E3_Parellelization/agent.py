import os, json, re 
import mlflow
from dotenv import load_dotenv

# MFLOW + OpenTelemetry Tracing Imports must be improted before the ADK imports
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

load_dotenv()

# Configuration
NUM_SUMMARIZE_AGENTS = int(os.getenv("NUM_SUMMARIZE_AGENTS", "10"))  # Default to 10 agents

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

# --- 4. Add Attributes to a Trace Span (New Steps) ---

# Get a tracer instance (always necessary to create spans)
tracer = trace.get_tracer(__name__)

# Start an MLflow Run to associate the trace with
with mlflow.start_run(experiment_id=experiment_id) as run:
    
    # Create the root span for the operation
    with tracer.start_as_current_span("parallel_data_processing") as span:
        
        # --- Add Attributes to the Span Here ---
        
        # 1. Attribute for the environment/context
        span.set_attribute("environment", "dev")
        
        # 2. Attribute for resource usage (numerical)
        span.set_attribute("number_of_agents", NUM_SUMMARIZE_AGENTS)
        
        # 3. Attribute for the input data source
        # span.set_attribute("data.source.bucket", "s3://my-ml-data")
        
        # 4. Attribute for a specific configuration detail (boolean)
        # span.set_attribute("use_caching", True)
        
        print(f"Executing operation with span: {span.context.span_id}")
        
        # Simulate the work being traced
        # ... Your parallelization logic goes here ...
        
from google.adk.agents import LlmAgent, ParallelAgent, SequentialAgent, LoopAgent
from google.adk.tools import google_search
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.tool_context import ToolContext
from typing import Optional
from google.genai import types
# from .tools import calculator_tool, read_data_tool, list_example_files_tool, get_processing_status_tool, update_processing_status_tool, assign_file_for_work_tool, get_work_assignments_tool, complete_assignment_tool

# Import agent factory functions
from .agents import (
    create_file_todo_list_agent,
    create_plan_and_assign_tasks_agent,
    create_document_analysis_agent,
    create_merger_agent,
)

print("Tracing complete.")
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
plan_and_assign_tasks_agent = create_plan_and_assign_tasks_agent(num_agents=NUM_SUMMARIZE_AGENTS)

# Dynamically create the specified number of DocumentAnalyzer agents
# Each agent encapsulates chunking internally and can run in parallel
document_analysis_agents = [
    create_document_analysis_agent(i) 
    for i in range(1, NUM_SUMMARIZE_AGENTS + 1)
]

merger_agent = create_merger_agent()

print(f"[Config] Using {NUM_SUMMARIZE_AGENTS} DocumentAnalyzer agent(s) with internal chunking")


# --- Create Composite Agents ---

# Parallel agent that runs multiple DocumentAnalyzer agents concurrently
# Each DocumentAnalyzer has internal chunking and analysis loops
parallel_document_analyzers = ParallelAgent(
    name="ParallelDocumentAnalyzerAgent",
    sub_agents=document_analysis_agents,
    description=f"Runs {NUM_SUMMARIZE_AGENTS} DocumentAnalyzer agent(s) with internal chunking in parallel."
)

# Loop agent that repeatedly assigns and processes pending files
file_processing_loop = LoopAgent(
    name="FileProcessingLoop",
    sub_agents=[plan_and_assign_tasks_agent, parallel_document_analyzers],
    max_iterations=10,
    description="Repeatedly assigns pending files to DocumentAnalyzer agents and processes them until all are completed."
)


# --- Create Main Sequential Pipeline ---
sequential_pipeline_agent = SequentialAgent(
    name="FileExtractionPipelineAgent",
    sub_agents=[
        file_todo_list_agent,      # 1. Initialize the todo list
        file_processing_loop,      # 2. Process documents: assign tasks then analyze in parallel
        merger_agent               # 3. Final synthesis of all results
    ],
    description="Coordinates document analysis using parallel DocumentAnalyzer agents with internal chunking and synthesizes the results."
)

root_agent = sequential_pipeline_agent