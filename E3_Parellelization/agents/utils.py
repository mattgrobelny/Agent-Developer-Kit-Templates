"""Shared utility functions for agents."""


def exit_loop(tool_context):
    """
    Exit a loop iteration by triggering escalation.
    
    Call this function ONLY when all tasks have been processed,
    signaling the iterative process should end.
    
    Args:
        tool_context: The tool context from the agent framework
        
    Returns:
        Empty dict (tools should return JSON-serializable output)
    """
    print(f"  [Tool Call] exit_loop triggered by {tool_context.agent_name}")
    tool_context.actions.escalate = True
    return {}
