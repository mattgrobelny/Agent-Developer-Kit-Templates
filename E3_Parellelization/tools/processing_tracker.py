"""Tool for checking file processing status from a tracking JSON file."""

import os
import json
from typing import Dict, Any
from google.adk.tools import FunctionTool


def get_processing_status(filename: str = None) -> str:
    """Check if a file has been processed by looking at a tracking JSON file.

    Args:
        filename: Optional specific filename to check status. If None, returns all tracked files.

    Returns:
        Processing status information in a formatted string
    """
    tools_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(tools_dir)
    tracking_file = os.path.join(parent_dir, "processing_tracker.json")
    
    # Initialize tracking file if it doesn't exist
    if not os.path.exists(tracking_file):
        return "No processing tracker found. Create one using track_file_processing() tool."
    
    try:
        with open(tracking_file, 'r', encoding='utf-8') as f:
            tracker = json.load(f)
    except Exception as e:
        return f"Error reading tracking file: {str(e)}"
    
    # If no filename specified, return all tracked files
    if filename is None:
        if not tracker.get("files"):
            return "No files currently being tracked"
        
        status_info = ["Processing Status Summary:"]
        for fname, info in sorted(tracker.get("files", {}).items()):
            status = info.get("status", "unknown")
            mod_dt = info.get("moddt", "unknown")
            status_info.append(f"  - {fname}: {status} (mod: {mod_dt})")
        
        return "\n".join(status_info)
    
    # Check specific file
    file_records = tracker.get("files", {})
    if filename not in file_records:
        return f"File '{filename}' not found in processing tracker"
    
    file_info = file_records[filename]
    return (f"File: {filename}\n"
            f"  Status: {file_info.get('status', 'unknown')}\n"
            f"  Modified: {file_info.get('moddt', 'unknown')}\n"
            f"  Processed: {file_info.get('processed_at', 'not yet')}")


def update_processing_status(filename: str, status: str) -> str:
    """Update the processing status of a file in the tracking JSON.

    Args:
        filename: Name of the file to update
        status: Processing status (e.g., 'pending', 'processing', 'completed', 'failed')

    Returns:
        Confirmation message
    """
    tools_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(tools_dir)
    tracking_file = os.path.join(parent_dir, "processing_tracker.json")
    example_data_dir = os.path.join(parent_dir, "example_data")
    
    # Check if file exists in example_data
    filepath = os.path.join(example_data_dir, filename)
    if not os.path.exists(filepath):
        return f"Error: File '{filename}' not found in example_data directory"
    
    # Initialize tracker if it doesn't exist
    if os.path.exists(tracking_file):
        try:
            with open(tracking_file, 'r', encoding='utf-8') as f:
                tracker = json.load(f)
        except Exception as e:
            return f"Error reading tracking file: {str(e)}"
    else:
        tracker = {"files": {}}
    
    # Update or create file entry
    mod_time = os.path.getmtime(filepath)
    tracker["files"][filename] = {
        "filename": filename,
        "moddt": mod_time,
        "status": status,
        "processed_at": os.path.getmtime(filepath) if status == "completed" else None
    }
    
    # Write back to tracking file
    try:
        with open(tracking_file, 'w', encoding='utf-8') as f:
            json.dump(tracker, f, indent=2)
        return f"Updated '{filename}' status to '{status}'"
    except Exception as e:
        return f"Error writing tracking file: {str(e)}"


get_processing_status_tool = FunctionTool(func=get_processing_status)
update_processing_status_tool = FunctionTool(func=update_processing_status)
