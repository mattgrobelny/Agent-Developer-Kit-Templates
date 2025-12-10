"""Synthesis Agent - combines research findings into a structured report."""

from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext

GEMINI_MODEL = "gemini-2.5-flash"


def aggregate_analysis_results_callback(callback_context: CallbackContext):
    """
    Prepares analysis results from all DocumentAnalyzer agents for synthesis.
    
    Uses best practices:
    - Reads agent-specific result keys (document_analysis_1, document_analysis_2, etc.)
    - Aggregates results into a single running_summary
    - Handles missing results gracefully
    """
    print("[SynthesisCallback] Aggregating results from all DocumentAnalyzer agents...")
    
    aggregated_summary = []
    
    # Iterate through potential agent results (1-6 based on default NUM_SUMMARIZE_AGENTS)
    for agent_num in range(1, 7):
        agent_result_key = f"document_analysis_{agent_num}"
        agent_result = callback_context.state.get(agent_result_key)
        
        if agent_result:
            print(f"[SynthesisCallback] Found analysis from DocumentAnalyzer{agent_num}")
            aggregated_summary.append(f"\n--- Analysis from DocumentAnalyzer{agent_num} ---\n{agent_result}")
        else:
            print(f"[SynthesisCallback] No analysis found for DocumentAnalyzer{agent_num} (agent may not have been assigned work)")
    
    if aggregated_summary:
        final_summary = "\n".join(aggregated_summary)
        print(f"[SynthesisCallback] Aggregated {len(aggregated_summary)} analysis result(s)")
        callback_context.state["aggregated_analysis"] = final_summary
    else:
        print("[SynthesisCallback] WARNING: No analysis results found from any agent")
        callback_context.state["aggregated_analysis"] = "No analysis results available"


def create_merger_agent():
    """Create and return the SynthesisAgent.
    
    Best Practices:
    - Uses before_agent_callback to aggregate results from parallel agents
    - Reads from agent-specific state keys (document_analysis_N)
    - Uses output_key to store final report in state
    - Includes defensive defaults in instruction template
    """
    return LlmAgent(
        name="SynthesisAgent",
        model=GEMINI_MODEL,
        instruction="""You are an AI Synthesis Agent. Your task is to create a final comprehensive report based on analyses performed by parallel DocumentAnalyzer agents.

AGGREGATED ANALYSIS RESULTS:
{aggregated_analysis:No analysis results available}

Based on the document analysis performed by multiple agents, create a structured final report that includes:

1. **Executive Summary**: Brief overview of key findings across all analyzed documents
2. **Key Findings**: Main points extracted from all document analyses, organized by theme
3. **Insights**: Connections and patterns identified across documents
4. **Cross-Document Themes**: Common themes or recurring topics across analyzed materials
5. **Recommendations** (if applicable): Based on all content analyzed
6. **Analysis Metadata**: 
   - Number of documents analyzed
   - Agents involved
   - Analysis completion status

The report must be grounded exclusively on the analysis results provided. Do not add external information.
Format the report in clear, professional markdown with proper sections and subsections.
""",
        description="Aggregates analyses from parallel DocumentAnalyzer agents into a comprehensive final report.",
        output_key="synthesized_report",
        before_agent_callback=aggregate_analysis_results_callback
    )
