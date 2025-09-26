"""FastAPI app that exposes Networking crew and LinkedIn utilities."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import urlparse, urlunparse

from fastapi import FastAPI, HTTPException
from pydantic import AnyHttpUrl, BaseModel, Field

from networking.clients import (
    BrightDataError,
    LinkedInFetcher,
    LinkedInSearchClient,
)
from networking.execution import run_networking_crew, select_profile


app = FastAPI(title="Networking Copilot API", version="0.1.0")


class CrewRequest(BaseModel):
    """Request payload for running the Networking crew."""

    linkedin_data: Union[Dict[str, Any], List[Dict[str, Any]]] = Field(
        ..., description="LinkedIn profile dictionary or list of dictionaries."
    )

    def primary_profile(self) -> Dict[str, Any]:
        """Pick the first profile from the payload."""

        if isinstance(self.linkedin_data, list):
            if not self.linkedin_data:
                raise ValueError("linkedin_data list must include at least one profile")
            return self.linkedin_data[0]
        if not isinstance(self.linkedin_data, dict):
            raise ValueError("linkedin_data must be an object or list of objects")
        return self.linkedin_data


class LinkedInRequest(BaseModel):
    url: AnyHttpUrl


class SearchRequest(BaseModel):
    first_name: str
    last_name: str
    additional_context: Optional[str] = Field(
        default=None,
        description="Plain-language hints about the target person (company, role, location, etc.).",
    )
    linkedin_url: AnyHttpUrl = Field(
        default="https://www.linkedin.com",
        description="Base LinkedIn URL used by the Bright Data search dataset.",
    )


@app.get("/health")
def healthcheck() -> Dict[str, str]:
    """Confirm the API is alive."""

    return {"status": "ok"}


@app.post("/run")
def run_crew(payload: CrewRequest) -> Dict[str, Any]:
    """Execute the Networking crew and return structured outputs for each task."""

    try:
        profile = payload.primary_profile()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    try:
        outputs = run_networking_crew(profile)
    except Exception as exc:  # pragma: no cover - surface crew execution issues
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return outputs


@app.post("/linkedin")
def fetch_linkedin(payload: LinkedInRequest) -> Dict[str, Any]:
    """Fetch LinkedIn profile data using the Bright Data dataset pipeline."""

    try:
        fetcher = LinkedInFetcher()
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    try:
        result = fetcher.fetch_profile(str(payload.url))
    except BrightDataError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return result


@app.post("/search")
def search_profile(payload: SearchRequest) -> Dict[str, Any]:
    """Search for a LinkedIn profile by name and optional context."""

    selected_profile, rationale, _ = _search_and_select(payload)
    return {
        "selected_profile": selected_profile,
        "selector_rationale": rationale,
    }


@app.post("/lookup")
def search_and_enrich(payload: SearchRequest) -> Dict[str, Any]:
    """Search for a person, fetch their profile, and run the Networking crew."""

    selected_profile, rationale, _ = _search_and_select(payload)

    profile_url = selected_profile.get("url")
    if not profile_url:
        raise HTTPException(status_code=502, detail="Selected profile does not include a LinkedIn URL")

    normalized_url = _normalize_linkedin_profile_url(profile_url)

    try:
        fetcher = LinkedInFetcher()
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    try:
        snapshot = fetcher.fetch_profile(normalized_url)
    except BrightDataError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    records = snapshot.get("records", [])
    if not records:
        raise HTTPException(status_code=502, detail="LinkedIn snapshot returned no profile records")

    profile_data = records[0]

    try:
        crew_outputs = run_networking_crew(profile_data)
    except Exception as exc:  # pragma: no cover - surface crew execution issues
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    person = {
        "url": normalized_url,
        "name": selected_profile.get("name"),
        "subtitle": selected_profile.get("subtitle"),
        "location": selected_profile.get("location"),
        "experience": selected_profile.get("experience"),
        "education": selected_profile.get("education"),
        "avatar": selected_profile.get("avatar"),
    }

    return {
        "person": person,
        "selector_rationale": rationale,
        "crew_outputs": crew_outputs,
    }


def _build_search_criteria(payload: SearchRequest) -> str:
    """Construct guidance for the selector agent based on provided hints."""

    hints = (payload.additional_context or "").strip()
    lines = [
        f"Target full name: {payload.first_name} {payload.last_name}.",
        "Use subtitle/headline, experience, education, and location to choose the best match.",
        "Strictly prioritize candidates based in major US tech hubs (San Francisco Bay Area, Seattle, New York City, Austin) or elsewhere in the United States before considering other regions.",
    ]

    if hints:
        lines.append(f"Additional hints from user: {hints}")
    else:
        lines.append(
            "No extra hints provided; fall back to technology-focused professionals in the United States if no direct match is available."
        )

    return "\n".join(lines)


def _search_and_select(payload: SearchRequest) -> Tuple[Dict[str, Any], Optional[str], Dict[str, Any]]:
    """Run Bright Data people search and select the best-matching profile."""

    try:
        search_client = LinkedInSearchClient()
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    try:
        search_result = search_client.search_people(
            payload.first_name,
            payload.last_name,
            search_url=str(payload.linkedin_url),
        )
    except BrightDataError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    candidates = search_result.get("records", [])
    if not candidates:
        raise HTTPException(status_code=404, detail="No LinkedIn candidates found for the provided name")

    criteria = _build_search_criteria(payload)

    try:
        selected_profile, rationale = select_profile(candidates, criteria)
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return selected_profile, rationale, search_result


def _normalize_linkedin_profile_url(url: str) -> str:
    """Convert localized LinkedIn domains to the canonical www.linkedin.com host."""

    parsed = urlparse(url.strip())
    if not parsed.netloc:
        raise HTTPException(status_code=422, detail="Invalid LinkedIn profile URL")

    host = parsed.netloc
    if host.endswith("linkedin.com") and host != "www.linkedin.com":
        host = "www.linkedin.com"

    scheme = parsed.scheme or "https"

    return urlunparse(parsed._replace(netloc=host, scheme=scheme))
