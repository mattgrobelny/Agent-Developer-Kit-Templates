# Bug Fix Report: `get_next_chunk` Document ID Filtering Issue

## Issue Summary
The `default_api.get_next_chunk` function repeatedly failed to return chunks for the specified `document_id`, instead providing content from other documents, including those not assigned to `DocumentAnalyzer1`. This prevented a complete analysis of assigned documents.

## Root Cause
The bug was in the initialization logic of `get_next_chunk()` in `E3_Parellelization/tools/chunking.py`:

**Problem**: When `document_id` was explicitly provided (e.g., calling `get_next_chunk(document_id="report_water_scarcity.txt", agent_id="DocumentAnalyzer1")`), subsequent calls with a **different** `document_id` were ignored.

**Why it happened**:
1. On the first call with `document_id="document_A.txt"`, the function initializes and loads chunks from document_A
2. On a subsequent call with `document_id="document_B.txt"`, the condition `if not state["chunks"] and state["current_document"] is None:` evaluates to **FALSE** because:
   - `state["chunks"]` still contains chunks from document_A (not empty)
   - `state["current_document"]` still contains "document_A.txt" (not None)
3. **Result**: The new `document_id` parameter is completely ignored, and the function continues returning chunks from document_A

This caused all DocumentAnalyzer agents to potentially retrieve chunks from wrong documents, as the agent-specific state was not being properly reset when a new document ID was requested.

## Solution
Added a new initialization step **before** the original logic to handle document switches:

```python
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
```

## Key Changes
1. **Document Switch Detection**: Check if the requested `document_id` differs from `state["current_document"]`
2. **State Reset**: When switching documents, completely reset the chunking state for that agent
3. **Immediate Reinitialization**: Load the newly requested document and return its first chunk
4. **Error Handling**: Return an error if the document cannot be initialized

## Impact
- Each DocumentAnalyzer agent can now correctly switch between assigned documents
- `DocumentAnalyzer1` will only retrieve chunks from documents assigned to it
- Parallel agents maintain independent chunking state per agent_id
- Complete analysis of all assigned documents is now possible

## Testing Recommendation
Run the following scenario to verify the fix:
1. Assign multiple documents to `DocumentAnalyzer1` via the todo list
2. Verify that `get_next_chunk(document_id="file1.txt", agent_id="DocumentAnalyzer1")` returns chunks from file1.txt
3. Then call `get_next_chunk(document_id="file2.txt", agent_id="DocumentAnalyzer1")` and verify it returns chunks from file2.txt (not file1.txt)
4. Confirm that different agent IDs maintain separate states

## File Modified
- `E3_Parellelization/tools/chunking.py` - Added document switch detection in `get_next_chunk()` function
