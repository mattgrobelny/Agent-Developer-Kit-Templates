"""Chunk Manager and Analyzer Agents - for document chunking and analysis."""

from google.adk.agents import LlmAgent
from .utils import exit_loop
from ..tools import get_next_chunk_tool 

GEMINI_MODEL = "gemini-2.5-flash"


def create_chunk_manager_agent():
    """Create and return the ChunkManagerAgent."""
    return LlmAgent(
        name="ChunkManager",
        model=GEMINI_MODEL,
        instruction="""You are managing the document chunking process. Your task is to:

1. Look at the todo_list_result to find the next file to process
2. Call the 'get_next_chunk' tool with that document name
3. The tool will return chunk_info with the following structure:
   - chunk_content: the text chunk
   - chunk_number: current chunk number
   - total_chunks: total number of chunks
   - more_chunks_exist: boolean indicating if more chunks remain

4. If more_chunks_exist is False for all chunks, you MUST call the 'exit_loop' tool to end the iteration

Output the chunk information for the ChunkAnalyzer agent to process.

TODO LIST: {todo_list_result}
""",
        tools=[get_next_chunk_tool, exit_loop],
        output_key="chunk_info"
    )


def create_chunk_analyzer_agent():
    """Create and return the ChunkAnalyzerAgent."""
    return LlmAgent(
        name="ChunkAnalyzer",
        model=GEMINI_MODEL,
        instruction="""You are a deep document analysis expert. Your task is to analyze chunks of text
    and merge findings into a running summary.

CHUNK INFORMATION: {chunk_info}
EXISTING RUNNING SUMMARY: {running_summary:No summary yet}

Based on the chunk provided, extract key information and merge it with the existing summary.

RULES:
1. Do NOT repeat content already in the running summary.
2. Only output the UPDATED running summary.
3. If the running summary is empty, output a new initial summary based on the current chunk.
4. Include metadata about which chunk you're processing.
""",
        description="Analyzes document chunks and updates the running summary.",
        output_key="running_summary"
    )
