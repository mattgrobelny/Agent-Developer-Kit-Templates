"""Chunk Manager and Analyzer Agents - for document chunking and analysis."""

from google.adk.agents import LlmAgent
from .utils import exit_loop
from tools import get_next_chunk_tool 
GEMINI_MODEL = "gemini-2.5-flash"


def create_chunk_manager_agent():
    """Create and return the ChunkManagerAgent."""
    return LlmAgent(
        name="ChunkManager",
        model=GEMINI_MODEL,
        instruction="""Call the 'get_next_chunk' tool for the document 'my_research_doc.txt'.
    
    If the tool reports 'more_chunks_exist' is False, you MUST call the 'exit_loop' tool.
    
    If a chunk is returned, store the chunk content in the state variable 'chunk_content'. 
    Do not output any text unless the tool is called.
    """,
        tools=[get_next_chunk_tool, exit_loop],
        output_key="chunk_content"
    )


def create_chunk_analyzer_agent():
    """Create and return the ChunkAnalyzerAgent."""
    return LlmAgent(
        name="ChunkAnalyzer",
        model=GEMINI_MODEL,
        instruction="""You are a deep document analysis expert. Your task is to analyze the CURRENT CHUNK of text
    and merge its findings into the EXISTING RUNNING SUMMARY. 

    EXISTING RUNNING SUMMARY: {running_summary}
    CURRENT CHUNK CONTENT: {chunk_content}

    RULES:
    1. Do NOT repeat content already in the running summary.
    2. Only output the UPDATED running summary.
    3. If the running summary is empty, output a new initial summary based on the current chunk.
    """,
        description="Analyzes a single document chunk and updates the running summary.",
        output_key="running_summary"
    )
