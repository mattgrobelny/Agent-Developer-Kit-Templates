"""Tool for listing files in the example_data directory."""

import os
import json
from google.adk.tools import FunctionTool


def list_example_files() -> str:
    """List all files in the example_data directory with metadata.

    Returns:
        Formatted string with list of files and their metadata (size, modification time)
    """
    tools_dir = os.path.dirname(__file__)
    example_data_dir = os.path.join(os.path.dirname(tools_dir), "example_data")
    
    if not os.path.exists(example_data_dir):
        return f"Error: example_data directory not found at {example_data_dir}"
    
    try:
        files = os.listdir(example_data_dir)
        if not files:
            return "No files found in example_data directory"
        
        file_info = []
        for filename in sorted(files):
            filepath = os.path.join(example_data_dir, filename)
            if os.path.isfile(filepath):
                size = os.path.getsize(filepath)
                mod_time = os.path.getmtime(filepath)
                file_info.append(f"  - {filename} ({size} bytes, modified: {mod_time})")
        
        if not file_info:
            return "No regular files found in example_data directory"
        
        return "Files in example_data:\n" + "\n".join(file_info)
    except Exception as e:
        return f"Error listing files: {str(e)}"


list_example_files_tool = FunctionTool(func=list_example_files)
