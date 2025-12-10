"""Synthesis Agent - combines research findings into a structured report."""

from google.adk.agents import LlmAgent

GEMINI_MODEL = "gemini-2.5-flash"


def create_merger_agent():
    """Create and return the SynthesisAgent."""
    return LlmAgent(
        name="SynthesisAgent",
        model=GEMINI_MODEL,
        instruction="""You are an AI Synthesis Agent. You will combine the research findings from multiple agents into a single, coherent report.
You must strictly base your synthesis on the provided research findings, without introducing any external information. 
Here are the research findings to synthesize:
- From ReadSummarizeFilesAgent1: {ReadSummarizeFilesAgent1_result}
- From ReadSummarizeFilesAgent2: {ReadSummarizeFilesAgent2_result}
Your final output should be a structured report summarizing the key insights from each research finding, with clear attributions to the respective agents.
Make sure to clearly cite which agent provided which piece of information.
""",
        description="Combines research findings from parallel agents into a structured report.",
        output_key="synthesized_report"
    )
