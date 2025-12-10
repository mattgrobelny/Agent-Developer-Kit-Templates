"""Tool for reading example data files from the example_data directory."""

import os
from google.adk.tools import FunctionTool


def read_data(filename: str = None) -> str:
    """Read example data files from the example_data directory.

    Args:
        filename: Optional specific filename to read. If None, lists all files in the directory.

    Returns:
        Content of the requested file or list of available files
    """
    # Get the parent directory of the tools directory
    tools_dir = os.path.dirname(__file__)
    example_data_dir = os.path.join(os.path.dirname(tools_dir), "example_data")
    
    if not os.path.exists(example_data_dir):
        return f"Error: example_data directory not found at {example_data_dir}"
    
    # If no filename specified, list all files
    if filename is None:
        files = os.listdir(example_data_dir)
        return f"Available files in example_data:\n" + "\n".join(files)
    
    # Read specific file
    filepath = os.path.join(example_data_dir, filename)
    
    # Security check: ensure the file is within example_data directory
    if not os.path.abspath(filepath).startswith(os.path.abspath(example_data_dir)):
        return "Error: Invalid file path"
    
    if not os.path.exists(filepath):
        return f"Error: File '{filename}' not found in example_data directory"
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception as e:
        return f"Error reading file: {str(e)}"


read_data_tool = FunctionTool(func=read_data)
