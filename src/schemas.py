"""Pydantic models for structured agent outputs."""

from typing import Literal, List, Dict
from pydantic import BaseModel, Field


class AgentAnalysis(BaseModel):
    """Structured output from a specialist agent's analysis."""
    
    agent_name: str = Field(..., description="Name of the agent (e.g., 'DBA', 'Network Engineer')")
    status: Literal["Critical", "Warning", "Healthy"] = Field(
        ..., 
        description="Severity status of the issue detected"
    )
    hypothesis: str = Field(
        ..., 
        description="One sentence summary of the problem identified",
        min_length=10
    )
    evidence_cited: List[str] = Field(
        ..., 
        description="Quotes from the logs that support the hypothesis",
        min_items=1
    )
    confidence_score: float = Field(
        ..., 
        ge=0.0, 
        le=1.0,
        description="Confidence level in the hypothesis (0.0 to 1.0)"
    )
    reasoning: str = Field(
        ..., 
        description="Detailed explanation of the analysis and why this hypothesis was formed",
        min_length=50
    )


class JudgeVerdict(BaseModel):
    """Structured output from the Judge agent's final decision."""
    
    root_cause_headline: str = Field(
        ..., 
        description="The one-sentence summary of the failure",
        min_length=20
    )
    root_cause_agent: str = Field(
        ..., 
        description="The agent who found the PRIMARY failure (e.g., 'Code Auditor', 'DBA', 'Network Engineer')"
    )
    scenarios_logic: str = Field(
        ..., 
        description="Explain the chain: Trigger -> Mechanism -> Symptom",
        min_length=50
    )
    remediation_plan: str = Field(
        ..., 
        description="Specific technical steps to fix the root cause (e.g., 'Wrap JSON parsing in try/finally')",
        min_length=30
    )