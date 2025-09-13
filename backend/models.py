from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class AnalysisRequest(BaseModel):
    """
    Defines the shape of an incoming request to the Veracity Engine API.
    """

    url: HttpUrl = Field(
        ...,  # The '...' makes this field required
        title="URL to be analyzed",
        description="A valid HTTP or HTTPS URL pointing to the content for analysis.",
    )


class Verdict(str, Enum):
    """
    Enumeration for the final verdict categories.
    Using an Enum makes the code safer and more readable than raw strings.
    """

    VERIFIED = "Verified"
    CAUTION = "Caution"
    UNRELIABLE = "Unreliable"
    DANGER = "Danger"


class SafeBrowsingResult(BaseModel):
    """
    Represents the structured result from the Google Safe Browsing API.
    """

    threat_type: str = Field(
        ...,
        description="The type of threat found, e.g., 'MALWARE', 'SOCIAL_ENGINEERING', or 'THREAT_TYPE_UNSPECIFIED'.",
    )
    details: dict[str, Any] = Field(
        default_factory=dict, description="Additional details provided by the API."
    )


class FactCheckResult(BaseModel):
    """
    Represents a single fact-check result from the Google Fact Check Tools API.
    """

    publisher: str = Field(
        ..., description="The name of the fact-checking organization."
    )
    claim: str = Field(..., description="The claim that was reviewed.")
    rating: str = Field(
        ..., description="The rating given by the publisher, e.g., 'True', 'False'."
    )
    review_url: HttpUrl = Field(
        ..., description="A URL to the full fact-check article."
    )


class GeminiAnalysis(BaseModel):
    """
    Represents the raw structured analysis from the Gemini Pro API.
    """

    credibility_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="The AI's estimated credibility score (0-100).",
    )
    summary: str = Field(
        ..., description="The AI-generated one-sentence neutral summary."
    )
    detected_flags: list[str] = Field(
        default_factory=list,
        description="A list of potential misinformation flags, e.g., 'emotionally_charged'.",
    )
    reasoning: str = Field(
        ..., description="The AI's reasoning for its score and flags."
    )


class AnalysisResponse(BaseModel):
    """
    Defines the shape of the JSON response sent back by the API.
    """

    veracity_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="The final calculated credibility score from 0 (low) to 100 (high).",
    )
    verdict: Verdict = Field(..., description="The overall verdict category.")
    summary: str = Field(
        ..., description="A one-sentence neutral summary of the content."
    )
    flags: list[str] = Field(
        default_factory=list,
        description="A list of flags indicating potential misinformation tactics.",
    )

    # Detailed breakdown from integrated services
    safe_browsing: SafeBrowsingResult
    fact_checks: list[FactCheckResult]
    raw_ai_analysis: GeminiAnalysis
