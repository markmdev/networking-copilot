"""Pydantic schemas that describe structured outputs for Networking crew tasks."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class LinkedInProfileAnalyzerOutput(BaseModel):
    """Structured insight payload produced by the analyzer task."""

    profile_name: Optional[str] = Field(
        default=None, description="Full name parsed from the LinkedIn profile."
    )
    headline: Optional[str] = Field(
        default=None, description="Headline or position string shown on LinkedIn."
    )
    current_title: Optional[str] = Field(
        default=None, description="Current role or title held by the person."
    )
    current_company: Optional[str] = Field(
        default=None, description="Company associated with the current role."
    )
    location: Optional[str] = Field(
        default=None, description="Geographic location if available."
    )
    highlights: List[str] = Field(
        ...,
        description=(
            "Exactly ten bullet points covering experience, skills, education, "
            "recent activity, awards, and any compelling networking insights."
        ),
        min_length=10,
        max_length=10,
    )

    @field_validator("highlights")
    @classmethod
    def strip_highlights(cls, highlights: List[str]) -> List[str]:
        """Ensure highlight strings are trimmed for clean downstream rendering."""

        return [item.strip() for item in highlights]


class SummaryOutput(BaseModel):
    """Two sentence summary packaged for UI consumption."""

    summary: str = Field(
        ..., description="Exactly two sentences summarising the professional profile."
    )
    key_highlights: List[str] = Field(
        ...,
        description="Top three supporting facts referenced in the summary.",
        min_length=3,
        max_length=3,
    )

    @field_validator("summary")
    @classmethod
    def ensure_two_sentences(cls, value: str) -> str:
        """Best-effort guard so the copy stays concise."""

        sentences = [sentence.strip() for sentence in value.split(".") if sentence.strip()]
        if len(sentences) != 2:
            raise ValueError("summary must contain exactly two sentences")
        return value.strip()


class IcebreakerItem(BaseModel):
    """Single conversation starter annotated with its tone."""

    category: Literal["professional", "educational", "industry", "interest", "personal"]
    prompt: str = Field(..., description="Conversation opener phrased as a natural question.")


class IcebreakerOutput(BaseModel):
    """Collection of conversation starters spread across styles."""

    icebreakers: List[IcebreakerItem] = Field(
        ...,
        description="Three to five prompts covering a mix of categories.",
        min_length=3,
        max_length=5,
    )


class ProfileSelectionOutput(BaseModel):
    """Chosen LinkedIn profile from a candidate set."""

    selected_profile: Dict[str, Any] = Field(
        ...,
        description="Single LinkedIn profile record that best matches the search criteria.",
    )
    rationale: Optional[str] = Field(
        default=None,
        description="Short explanation of why this profile was selected.",
    )
