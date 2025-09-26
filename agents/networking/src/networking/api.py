"""FastAPI app that exposes Networking crew and LinkedIn utilities."""

from __future__ import annotations

import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import urlparse, urlunparse

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import AnyHttpUrl, BaseModel, Field

from networking.clients import (
    BrightDataError,
    LinkedInFetcher,
    LinkedInSearchClient,
)
from networking.execution import run_networking_crew, select_profile
from networking.image_extractor import extract_from_image


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


@app.post("/extract-image")
async def extract_image(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Extract structured data from an uploaded badge/business card image."""

    if not file.filename:
        raise HTTPException(status_code=422, detail="Filename is required")

    suffix = Path(file.filename).suffix or ".png"
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=415, detail="Only image uploads are supported")

    tmp_path = None
    try:
        with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name

        extracted, markdown = extract_from_image(tmp_path)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

    return {
        "filename": file.filename,
        "extracted": extracted,
        "markdown": markdown,
    }


@app.post("/extract-and-lookup")
async def extract_and_lookup(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Extract info from an image, then run lookup on the parsed person."""

    print(f"🔥 extract-and-lookup called with file: {file.filename}")
    print(f"📁 File details: size={file.size}, content_type={file.content_type}")
    
    try:
        print("📸 Step 1: Calling extract_image...")
        extraction = await extract_image(file)  # type: ignore[arg-type]
        print(f"✅ Step 1 complete: {extraction.get('filename', 'unknown')}")
        
        extracted = extraction["extracted"]
        print(f"📄 Extracted data: {extracted}")

        basic_info = extracted.get("basic_info", {}) if isinstance(extracted, dict) else {}
        names = basic_info.get("names", "") if isinstance(basic_info, dict) else ""
        print(f"👤 Names extracted: '{names}'")
        
        if not names:
            print("❌ No names found in extracted data")
            raise HTTPException(status_code=502, detail="Unable to extract names from the image")

        parts = names.split()
        if len(parts) == 1:
            first_name, last_name = parts[0], parts[0]
        else:
            first_name, last_name = parts[0], " ".join(parts[1:])
        
        print(f"✂️ Name parts: first='{first_name}', last='{last_name}'")

        additional_context = extracted.get("links", {}) if isinstance(extracted, dict) else {}
        context_parts = []
        if isinstance(additional_context, dict):
            for key in ("linkedin", "website", "github"):
                value = additional_context.get(key)
                if value:
                    context_parts.append(f"{key}: {value}")
        company = basic_info.get("company") if isinstance(basic_info, dict) else None
        if company:
            context_parts.append(f"company: {company}")
        
        print(f"🔍 Search context: {context_parts}")

        search_payload = SearchRequest(
            first_name=first_name,
            last_name=last_name,
            additional_context=", ".join(context_parts) or None,
        )

        print("🔎 Step 2: Searching and selecting profile...")
        selected_profile, rationale, _ = _search_and_select(search_payload)
        print(f"✅ Step 2 complete: Selected {selected_profile.get('name', 'unknown')}")

        profile_url = selected_profile.get("url")
        if not profile_url:
            print("❌ No URL in selected profile")
            raise HTTPException(status_code=502, detail="Selected profile does not include a LinkedIn URL")

        normalized_url = _normalize_linkedin_profile_url(profile_url)
        print(f"🔗 Normalized URL: {normalized_url}")

        try:
            print("📊 Step 3: Fetching LinkedIn profile...")
            fetcher = LinkedInFetcher()
        except ValueError as exc:
            print(f"❌ Failed to create LinkedInFetcher: {exc}")
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        try:
            snapshot = fetcher.fetch_profile(normalized_url)
            print(f"✅ Step 3 complete: Got {len(snapshot.get('records', []))} records")
        except BrightDataError as exc:
            print(f"❌ BrightData error: {exc}")
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        records = snapshot.get("records", [])
        if not records:
            print("❌ No records in LinkedIn snapshot")
            raise HTTPException(status_code=502, detail="LinkedIn snapshot returned no profile records")

        profile_data = records[0]
        print(f"👤 Profile data keys: {list(profile_data.keys()) if isinstance(profile_data, dict) else 'not a dict'}")

        try:
            print("🤖 Step 4: Running networking crew...")
            crew_outputs = run_networking_crew(profile_data)
            print(f"✅ Step 4 complete: Generated outputs for {len(crew_outputs)} tasks")
        except Exception as exc:  # pragma: no cover - surface crew execution issues
            print(f"❌ Crew execution failed: {exc}")
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

        result = {
            "filename": extraction["filename"],
            "markdown": extraction["markdown"],
            "person": person,
            "selector_rationale": rationale,
            "crew_outputs": crew_outputs,
        }
        
        print("🎉 extract-and-lookup completed successfully!")
        return result
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as exc:
        print(f"💥 Unexpected error in extract-and-lookup: {exc}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(exc)}") from exc


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
