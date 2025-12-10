import os
import mlflow
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

load_dotenv()

# 1. Setup MLflow Experiment
# Ensure the experiment exists and get its ID.
# If you don't create one, MLflow uses '0' (Default), but it's safer to be explicit.
mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"))
experiment_name = "E0_ADK_MFlow_Traces"
experiment = mlflow.get_experiment_by_name(experiment_name)
if experiment is None:
    experiment_id = mlflow.create_experiment(experiment_name)
else:
    experiment_id = experiment.experiment_id

# 2. Configure the exporter
# The endpoint should be the full URL: http://host:port/v1/traces
MLFLOW_SERVER_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")

otlp_exporter = OTLPSpanExporter(
    endpoint=f"{MLFLOW_SERVER_URI}/v1/traces",
    headers={
        "Content-Type": "application/x-protobuf",
        "x-mlflow-experiment-id": experiment_id,  # <--- THIS IS THE KEY FIX
    }
)

# 3. Configure the tracer provider
tracer_provider = TracerProvider()
tracer_provider.add_span_processor(SimpleSpanProcessor(otlp_exporter))
trace.set_tracer_provider(tracer_provider)


def calculator(a: float, b: float) -> str:
    """Add two numbers and return the result.

    Args:
        a: First number
        b: Second number

    Returns:
        The sum of a and b
    """
    return str(a + b)


calculator_tool = FunctionTool(func=calculator)

root_agent = LlmAgent(
    name="MathAgent",
    model="gemini-2.5-flash",
    instruction=(
        "You are a helpful assistant that can do math. "
        "When asked a math problem, use the calculator tool to solve it."
    ),
    tools=[calculator_tool],
)