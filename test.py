import asyncio
import os
import sys

# --- 1. OpenTelemetry/MLflow Setup ---
# ADK uses OpenTelemetry, so we must configure the OTLP exporter 
# to point to the MLflow server's OTLP endpoint.

try:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    
    # Define the OTLP endpoint for your MLflow Server
    # Assumes MLflow is running on localhost:5000 as per the Dockerfile/setup steps
    MLFLOW_OTLP_ENDPOINT = "http://localhost:5000/v1/traces"

    # 1. Configure the OTLP Exporter
    exporter = OTLPSpanExporter(
        endpoint=MLFLOW_OTLP_ENDPOINT,
        timeout=5 # Set a timeout for the export operation
    )

    # 2. Set the Global Tracer Provider
    provider = TracerProvider()
    processor = SimpleSpanProcessor(exporter)
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
    
    print(f"✨ OpenTelemetry configured to export traces to: {MLFLOW_OTLP_ENDPOINT}")

except ImportError:
    print("⚠️ OpenTelemetry/MLflow tracing dependencies not found. Please run: pip install opentelemetry-sdk opentelemetry-exporter-otlp mlflow")
    sys.exit(1)
    
# --- 2. Google ADK Agent Setup ---
# ADK components must be imported *after* the OpenTelemetry setup is complete.
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from google.adk.runners import Runner

# Load environment variables from a .env file if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️ 'python-dotenv' not installed. Consider running: pip install python-dotenv for .env support.")

# NOTE: Ensure your GEMINI_API_KEY is set as an environment variable
# ADK requires a Gemini model key for the LlmAgent.
if not os.getenv("GEMINI_API_KEY"):
    print("\n🚨 ERROR: GEMINI_API_KEY environment variable is not set.")
    print("Please set it before running the agent (e.g., export GEMINI_API_KEY=... or set it in a .env file).")
    sys.exit(1)

# Define a simple function (tool) for the agent to use
def get_current_time(timezone: str) -> str:
    """Returns the current time in the specified timezone, e.g., 'America/Chicago'."""
    import datetime
    import pytz
    try:
        tz = pytz.timezone(timezone)
        return datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S %Z%z")
    except Exception as e:
        return f"Error: Could not find timezone {timezone}"

# Wrap the function in an ADK Tool
time_tool = FunctionTool(func=get_current_time)

# Define the main ADK Agent
root_agent = LlmAgent(
    name="TimeQueryAgent",
    model="gemini-2.5-flash",  # Use a Gemini model
    tools=[time_tool],
    instruction="You are a helpful assistant that answers questions about the current time by using the available tool. Always specify the timezone in your response."
)

# --- 3. Run the Agent ---
async def run_tracing_agent():
    print("-" * 50)
    print("🚀 Starting ADK Agent Run...")

    user_query = "What is the current time in London, UK?"
    
    # The Runner will execute the agent and automatically generate OTel spans
    # for the LLM call and the Tool call.
    result = await Runner.run(root_agent, user_query)

    print("\n✅ Agent Run Complete.")
    print(f"User Query: {user_query}")
    print(f"Final Output: {result.final_output}")
    print("-" * 50)
    print(f"Check the MLflow UI at http://localhost:5000 to see the full trace!")


if __name__ == "__main__":
    try:
        asyncio.run(run_tracing_agent())
    except KeyboardInterrupt:
        print("\nExiting application.")