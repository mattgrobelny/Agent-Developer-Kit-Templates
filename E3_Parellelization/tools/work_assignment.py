"""Tool for assigning files for work and managing work assignments."""

import os
import json
from datetime import datetime
from typing import List
from google.adk.tools import FunctionTool


def assign_file_for_work(filename: str, assigned_to: str, priority: str = "normal") -> str:
    """Assign a file for work to a specific agent or worker.

    Args:
        filename: Name of the file to assign
        assigned_to: Name/identifier of the agent or worker assigned to process the file
        priority: Priority level (low, normal, high, critical) - default is normal

    Returns:
        Confirmation message with assignment details
    """
    tools_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(tools_dir)
    assignments_file = os.path.join(parent_dir, "work_assignments.json")
    example_data_dir = os.path.join(parent_dir, "example_data")
    
    # Check if file exists in example_data
    filepath = os.path.join(example_data_dir, filename)
    if not os.path.exists(filepath):
        return f"Error: File '{filename}' not found in example_data directory"
    
    # Validate priority
    valid_priorities = ["low", "normal", "high", "critical"]
    if priority not in valid_priorities:
        return f"Error: Invalid priority '{priority}'. Must be one of: {', '.join(valid_priorities)}"
    
    # Initialize assignments if file doesn't exist
    if os.path.exists(assignments_file):
        try:
            with open(assignments_file, 'r', encoding='utf-8') as f:
                assignments = json.load(f)
        except Exception as e:
            return f"Error reading assignments file: {str(e)}"
    else:
        assignments = {"assignments": []}
    
    # Create assignment entry
    assignment = {
        "filename": filename,
        "assigned_to": assigned_to,
        "priority": priority,
        "assigned_at": datetime.now().isoformat(),
        "status": "assigned"
    }
    
    # Check if file is already assigned and update or add new
    existing_index = None
    for i, asgn in enumerate(assignments.get("assignments", [])):
        if asgn["filename"] == filename:
            existing_index = i
            break
    
    if existing_index is not None:
        assignments["assignments"][existing_index] = assignment
        action = "reassigned"
    else:
        assignments["assignments"].append(assignment)
        action = "assigned"
    
    # Write back to file
    try:
        with open(assignments_file, 'w', encoding='utf-8') as f:
            json.dump(assignments, f, indent=2)
        return (f"File '{filename}' {action} to '{assigned_to}' "
                f"with priority '{priority}'")
    except Exception as e:
        return f"Error writing assignments file: {str(e)}"


def get_work_assignments(assigned_to: str = None) -> str:
    """Get work assignments, optionally filtered by assignee.

    Args:
        assigned_to: Optional filter for specific agent/worker. If None, returns all assignments.

    Returns:
        Formatted string with assignment details
    """
    tools_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(tools_dir)
    assignments_file = os.path.join(parent_dir, "work_assignments.json")
    
    if not os.path.exists(assignments_file):
        return "No work assignments found. Use assign_file_for_work() to create assignments."
    
    try:
        with open(assignments_file, 'r', encoding='utf-8') as f:
            assignments = json.load(f)
    except Exception as e:
        return f"Error reading assignments file: {str(e)}"
    
    all_assignments = assignments.get("assignments", [])
    
    # Filter by assignee if specified
    if assigned_to:
        filtered = [a for a in all_assignments if a["assigned_to"] == assigned_to]
        if not filtered:
            return f"No assignments found for '{assigned_to}'"
        assignments_to_display = filtered
        title = f"Assignments for '{assigned_to}':"
    else:
        if not all_assignments:
            return "No work assignments found"
        assignments_to_display = all_assignments
        title = "All Work Assignments:"
    
    # Sort by priority (critical, high, normal, low)
    priority_order = {"critical": 0, "high": 1, "normal": 2, "low": 3}
    assignments_to_display.sort(
        key=lambda x: (priority_order.get(x.get("priority", "normal"), 999), 
                       x.get("assigned_at", ""))
    )
    
    result = [title]
    for asgn in assignments_to_display:
        result.append(
            f"  - {asgn['filename']} → {asgn['assigned_to']} "
            f"[{asgn['priority'].upper()}] ({asgn['status']})"
        )
    
    return "\n".join(result)


def complete_assignment(filename: str) -> str:
    """Mark a file assignment as completed.

    Args:
        filename: Name of the file whose assignment is being completed

    Returns:
        Confirmation message
    """
    tools_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(tools_dir)
    assignments_file = os.path.join(parent_dir, "work_assignments.json")
    
    if not os.path.exists(assignments_file):
        return "No work assignments found"
    
    try:
        with open(assignments_file, 'r', encoding='utf-8') as f:
            assignments = json.load(f)
    except Exception as e:
        return f"Error reading assignments file: {str(e)}"
    
    # Find and update assignment
    for asgn in assignments.get("assignments", []):
        if asgn["filename"] == filename:
            asgn["status"] = "completed"
            asgn["completed_at"] = datetime.now().isoformat()
            
            try:
                with open(assignments_file, 'w', encoding='utf-8') as f:
                    json.dump(assignments, f, indent=2)
                return f"Assignment for '{filename}' marked as completed"
            except Exception as e:
                return f"Error updating assignments file: {str(e)}"
    
    return f"No assignment found for file '{filename}'"


assign_file_for_work_tool = FunctionTool(func=assign_file_for_work)
get_work_assignments_tool = FunctionTool(func=get_work_assignments)
complete_assignment_tool = FunctionTool(func=complete_assignment)
