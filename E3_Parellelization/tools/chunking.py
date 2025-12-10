from google.adk.tools import FunctionTool
from .read_data import read_data, read_data_tool


class DocumentChunker:
    # A class to hold the chunks across tool calls (state persistence)
    chunks = []
    current_index = 0


def get_next_chunk(document_id: str) -> dict:
    """
    Retrieves the next chunk of the specified document for analysis.
    
    Args:
        document_id: The identifier/name of the document to chunk
    
    Returns:
        Dictionary with chunk content and metadata, or signal when finished
    """
    # 1. Initialization (Run only on the first call)
    if not DocumentChunker.chunks:
        # NOTE: Implement your actual file reading and splitting logic here.
        full_text = read_data(document_id) 
        
        # Example of simple chunking logic: split into 2000-character segments
        chunk_size = 2000
        DocumentChunker.chunks = [
            full_text[i:i + chunk_size] for i in range(0, len(full_text), chunk_size)
        ]
        DocumentChunker.current_index = 0
        
    # 2. Retrieval and State Check
    if DocumentChunker.current_index < len(DocumentChunker.chunks):
        chunk = DocumentChunker.chunks[DocumentChunker.current_index]
        chunk_info = {
            "chunk_content": chunk,
            "chunk_number": DocumentChunker.current_index + 1,
            "total_chunks": len(DocumentChunker.chunks),
            "more_chunks_exist": True
        }
        DocumentChunker.current_index += 1
        return chunk_info
    else:
        # Reset state and signal the end
        DocumentChunker.chunks = []
        DocumentChunker.current_index = 0
        return {"more_chunks_exist": False}
    

get_next_chunk_tool = FunctionTool(func=get_next_chunk)