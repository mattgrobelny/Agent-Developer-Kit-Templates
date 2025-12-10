"""Calculator tool for basic arithmetic operations."""

from google.adk.tools import FunctionTool


def calculator(a: float, b: float) -> str:
    """Add two numbers and return the result.

    Args:
        a: First number
        b: Second number

    Returns:
        The sum of a and b
    """
    return str(a + b)


calculator_tool = FunctionTool(func=calculator)
