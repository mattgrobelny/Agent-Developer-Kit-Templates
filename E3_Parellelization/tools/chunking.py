from google.adk.tools import FunctionTool
from .read_data import read_data, read_data_tool


class DocumentChunker:
    """Manages document chunking state per agent to support parallel processing."""
    # Store state per agent_id: agent_id -> {chunks, current_index, current_document, ...}
    agent_states = {}


def _get_agent_state(agent_id: str) -> dict:
    """Get or initialize state for a specific agent."""
    if agent_id not in DocumentChunker.agent_states:
        DocumentChunker.agent_states[agent_id] = {
            "chunks": [],
            "current_index": 0,
            "current_document": None,
            "documents_processed": set(),
            "all_documents": [],
            "current_document_index": 0
        }
    return DocumentChunker.agent_states[agent_id]


def get_next_chunk(document_id: str = None, agent_id: str = "default") -> dict:
    """
    Retrieves the next chunk of the specified document for analysis.
    
    Handles multiple documents sequentially, chunking each one.
    When document_id is None on first call, processes all available documents.
    
    Args:
        document_id: The identifier/name of the document to chunk. 
                    If None on first call, fetches all documents.
        agent_id: Unique identifier for the agent calling this function.
                 Each agent maintains separate chunking state.
    
    Returns:
        Dictionary with chunk content and metadata, or signal when finished
    """
    state = _get_agent_state(agent_id)
    
    # 1. Handle requests for a specific document that differs from the current one
    if document_id is not None and state["current_document"] != document_id:
        # Switch to the requested document by resetting and reinitializing
        state["chunks"] = []
        state["current_index"] = 0
        state["current_document"] = None
        state["documents_processed"] = set()
        state["all_documents"] = [document_id]
        state["current_document_index"] = 0
        _initialize_document(document_id, agent_id)
        
        # Return first chunk of the newly initialized document
        if state["chunks"]:
            chunk = state["chunks"][0]
            chunk_info = {
                "chunk_content": chunk,
                "chunk_number": 1,
                "total_chunks": len(state["chunks"]),
                "current_document": state["current_document"],
                "more_chunks_exist": True
            }
            state["current_index"] = 1
            return chunk_info
        else:
            return {"more_chunks_exist": False, "error": f"Could not initialize document '{document_id}'"}
    
    # 2. Initialization on first call (when no document is currently loaded)
    if not state["chunks"] and state["current_document"] is None:
        if document_id is None:
            # Get all documents from example_data
            try:
                all_docs_str = read_data()  # Call with no args to list files
                # Parse the file list
                lines = all_docs_str.split('\n')[1:]  # Skip header
                state["all_documents"] = [line.strip() for line in lines if line.strip()]
            except Exception as e:
                print(f"[{agent_id}] Error fetching document list: {e}")
                return {"more_chunks_exist": False, "error": str(e)}
        else:
            state["all_documents"] = [document_id]
        
        state["current_document_index"] = 0
        
        # Initialize first document if we have any
        if state["all_documents"]:
            _initialize_document(state["all_documents"][0], agent_id)
        else:
            return {"more_chunks_exist": False, "reason": "No documents found"}
    
    # 3. Check if current document has more chunks
    if state["current_index"] < len(state["chunks"]):
        chunk = state["chunks"][state["current_index"]]
        chunk_info = {
            "chunk_content": chunk,
            "chunk_number": state["current_index"] + 1,
            "total_chunks": len(state["chunks"]),
            "current_document": state["current_document"],
            "more_chunks_exist": True
        }
        state["current_index"] += 1
        return chunk_info
    
    # 4. Current document is done, move to next document
    else:
        state["documents_processed"].add(state["current_document"])
        state["current_document_index"] += 1
        
        # Check if there are more documents to process
        if state["current_document_index"] < len(state["all_documents"]):
            next_doc = state["all_documents"][state["current_document_index"]]
            _initialize_document(next_doc, agent_id)
            
            # Return first chunk of next document
            chunk = state["chunks"][0]
            chunk_info = {
                "chunk_content": chunk,
                "chunk_number": 1,
                "total_chunks": len(state["chunks"]),
                "current_document": state["current_document"],
                "document_changed": True,
                "more_chunks_exist": True
            }
            state["current_index"] = 1
            return chunk_info
        else:
            # All documents processed
            _reset_state(agent_id)
            return {
                "more_chunks_exist": False,
                "reason": "All documents processed",
                "documents_processed": list(state["documents_processed"])
            }


def _initialize_document(document_id: str, agent_id: str):
    """Initialize chunking for a new document with overlapping chunks."""
    state = _get_agent_state(agent_id)
    try:
        full_text = read_data(document_id)
        
        # Chunking logic: split into 2000-character segments with 5% overlap
        chunk_size = 2000
        overlap_percentage = 0.05  # 5% overlap
        overlap_size = int(chunk_size * overlap_percentage)
        step_size = chunk_size - overlap_size
        
        chunks = []
        for i in range(0, len(full_text), step_size):
            chunk = full_text[i:i + chunk_size]
            if chunk:  # Only add non-empty chunks
                chunks.append(chunk)
            # Stop if we've captured the rest of the document
            if i + chunk_size >= len(full_text):
                break
        
        state["chunks"] = chunks
        state["current_index"] = 0
        state["current_document"] = document_id
        print(f"[Chunking][{agent_id}] Initialized document '{document_id}' with {len(state['chunks'])} overlapping chunk(s)")
        print(f"[Chunking][{agent_id}] Chunk size: {chunk_size}, Overlap: {overlap_percentage*100}% ({overlap_size} chars), Step: {step_size}")
    except Exception as e:
        print(f"[Chunking][{agent_id}] Error reading document '{document_id}': {e}")
        state["chunks"] = []
        state["current_document"] = None


def _reset_state(agent_id: str):
    """Reset the chunker state for a specific agent."""
    if agent_id in DocumentChunker.agent_states:
        del DocumentChunker.agent_states[agent_id]


get_next_chunk_tool = FunctionTool(func=get_next_chunk)