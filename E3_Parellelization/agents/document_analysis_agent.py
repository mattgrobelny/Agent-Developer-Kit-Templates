"""
Document Analysis Agent - analyzes documents using chunking and summarization.

Best Practices Applied:
- Per-agent state isolation using agent_number in state keys
- Defensive state reading with .get() and defaults
- Agent-specific result storage (document_analysis_N)
- Callbacks that update shared state safely
"""

import time
import json
import re
from google.adk.agents import LlmAgent, LoopAgent
from google.adk.agents.callback_context import CallbackContext
from ..tools import read_data_tool, list_example_files_tool, get_processing_status_tool, get_next_chunk_tool


GEMINI_MODEL = "gemini-2.5-flash"


def update_document_analysis_callback(callback_context: CallbackContext):
    """
    Updates the document processing status after analysis is complete.
    
    Uses defensive state management:
    - Reads todo_list_result safely with fallbacks
    - Updates only tasks assigned to this agent
    - Stores agent-specific results in separate state keys
    """
    current_agent_name = callback_context.agent_name
    print(f"[Callback] Analysis completed by: {current_agent_name}")
    
    # Step 1: Safely read todo_list_result with multiple fallback strategies
    todo_list_raw = callback_context.state.get("todo_list_result")
    todo_list = []
    
    if isinstance(todo_list_raw, str):
        # Try to extract JSON from markdown code blocks first
        match = re.search(r"```json\s*([\s\S]*?)\s*```", todo_list_raw)
        if match:
            json_content = match.group(1)
        else:
            json_content = todo_list_raw
        
        try:
            todo_list = json.loads(json_content)
        except json.JSONDecodeError as e:
            print(f"[Callback] WARNING: Could not parse todo_list_result as JSON: {e}")
            return None
            
    elif isinstance(todo_list_raw, list):
        todo_list = todo_list_raw
    else:
        print(f"[Callback] WARNING: todo_list_result is empty or unexpected type: {type(todo_list_raw)}")
        return None

    # Step 2: Mark pending tasks assigned to this agent as completed
    tasks_updated = 0
    print(f"[Callback] Current agent name is '{current_agent_name}'")
    
    for i, task in enumerate(todo_list):
        if isinstance(task, dict):
            assigned_agent = task.get("assigned_agent")
            status = task.get("status")
            filename = task.get("filename", "unknown")
            
            print(f"[Callback] Task {i} Document: {filename}, Assigned: '{assigned_agent}', Status: {status}")

            # Update all pending tasks assigned to this agent
            if assigned_agent == current_agent_name and status == "pending":
                task["status"] = "completed"
                task["processed_at"] = time.time()
                tasks_updated += 1
                print(f"[Callback] ✓ Marked document {filename} as completed.")
    
    # Step 3: Update shared todo list in state
    if tasks_updated > 0:
        print(f"[Callback] SUCCESS: Updated {tasks_updated} task(s). Saving updated todo list to state.")
        callback_context.state["todo_list_result"] = todo_list
    else:
        print(f"[Callback] INFO: No pending tasks found for this agent.")
    
    # Step 4: Store agent-specific result using agent number for isolation
    # Extract agent number from name (e.g., "DocumentAnalyzer1" -> "1")
    agent_result_key = f"{current_agent_name}_completed_at"
    callback_context.state[agent_result_key] = time.time()
    print(f"[Callback] Stored completion timestamp in state key: {agent_result_key}")


def create_document_chunk_manager_agent(agent_number: int):
    """Create a chunk manager agent for a specific document analyzer."""
    agent_name = f"DocumentChunkManager{agent_number}"
    parent_agent_name = f"DocumentAnalyzer{agent_number}"
    
    return LlmAgent(
        name=agent_name,
        model=GEMINI_MODEL,
        instruction=f"""You are managing the document chunking process for {parent_agent_name}.

IMPORTANT: You are working for agent: {parent_agent_name}
AGENT_ID: DocumentAnalyzer{agent_number}

Your task:
1. Look at the todo_list_result to find documents assigned to '{parent_agent_name}': {{todo_list_result}}
2. ONLY process documents where assigned_agent == '{parent_agent_name}'
3. For each assigned document, call the 'get_next_chunk' tool with:
   - document_id: the document filename
   - agent_id: 'DocumentAnalyzer{agent_number}' (to maintain separate state per agent)
4. The tool will return chunk_info with: chunk_content, chunk_number, total_chunks, more_chunks_exist, current_document
5. When more_chunks_exist is False for all your documents, stop and let the analyzer finish

Output the chunk information for the analyzer to process.
Do not call exit_loop - that will be handled by the main loop control.
""",
        tools=[get_next_chunk_tool, read_data_tool, list_example_files_tool, get_processing_status_tool],
        output_key=f"chunk_info_{agent_number}"
    )


def create_document_chunk_analyzer_agent(agent_number: int):
    """Create a chunk analyzer agent for a specific document analyzer."""
    agent_name = f"DocumentChunkAnalyzer{agent_number}"
    parent_agent_name = f"DocumentAnalyzer{agent_number}"
    
    return LlmAgent(
        name=agent_name,
        model=GEMINI_MODEL,
        instruction=f"""You are analyzing document chunks for {parent_agent_name}.

IMPORTANT: You are working for agent: {parent_agent_name}

CHUNK INFORMATION: {{chunk_info_{agent_number}}}
EXISTING ANALYSIS: {{document_analysis_{agent_number}:No analysis yet}}

Based on the chunk provided, extract key information and merge it with the existing analysis.

ANALYSIS RULES:
1. Do NOT repeat content already in the existing analysis.
2. Only output the UPDATED analysis incorporating the new chunk.
3. If no existing analysis, create a new one based on the current chunk.
4. Include metadata: document name, chunk number being analyzed.
5. Extract: key findings, important data, themes, and patterns.

Output Format:
- Document: [name]
- Chunks Processed: [number]
- Key Findings:
  * [Finding 1]
  * [Finding 2]
  ...
- Running Analysis: [Comprehensive summary so far]
""",
        description=f"Analyzes document chunks for {parent_agent_name}",
        output_key=f"document_analysis_{agent_number}"
    )


def create_document_analysis_agent(agent_number: int):
    """
    Create a complete document analysis agent that uses chunking internally.
    
    This agent combines chunk management and analysis in a loop to process
    documents assigned to it through the todo list.
    
    Args:
        agent_number: Unique number for this agent (1, 2, 3, etc.)
    """
    agent_name = f"DocumentAnalyzer{agent_number}"
    
    chunk_manager = create_document_chunk_manager_agent(agent_number)
    chunk_analyzer = create_document_chunk_analyzer_agent(agent_number)
    
    # Create internal loop for chunk processing
    document_analysis_loop = LoopAgent(
        name=f"DocumentAnalysisLoop{agent_number}",
        sub_agents=[chunk_manager, chunk_analyzer],
        max_iterations=100,  # High limit to process all chunks for all assigned documents
        description=f"Processes document chunks for {agent_name}"
    )
    
    # Wrap in an LLM agent that handles the overall analysis and state updates
    return LlmAgent(
        name=agent_name,
        model=GEMINI_MODEL,
        instruction="""You are a Document Analysis Agent responsible for analyzing documents assigned to you.

ASSIGNED WORK: {todo_list_result}

Your workflow:
1. Process all documents assigned to you in the todo list
2. For each document, the chunk processing loop will handle chunking and analysis
3. Build a comprehensive summary of all your assigned documents
4. Return the final analysis for synthesis

Focus on extracting key insights, findings, and important data from each document.
Include document names and key themes in your analysis.
""",
        description=f"Analyzes assigned documents with chunking: {agent_name}",
        tools=[get_next_chunk_tool, read_data_tool, list_example_files_tool, get_processing_status_tool],
        output_key=f"document_analysis_{agent_number}",  # Use consistent naming for synthesis agent
        after_agent_callback=update_document_analysis_callback
    )
