from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

from openai import OpenAI

from networking.cache import get_cached_lookup, set_cached_lookup, save_person_record
from networking.clients import BrightDataError, LinkedInFetcher, LinkedInSearchClient
from networking.execution import run_networking_crew, select_profile
from networking.image_extractor import extract_from_bytes


@dataclass
class SearchPayload:
    first_name: str
    last_name: str
    additional_context: Optional[str] = None
    linkedin_url: str = "https://www.linkedin.com"


def _build_search_criteria(payload: SearchPayload) -> str:
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


def _normalize_linkedin_profile_url(url: str) -> str:
    from urllib.parse import urlparse, urlunparse

    parsed = urlparse(url.strip())
    if not parsed.netloc:
        raise ValueError("Invalid LinkedIn profile URL")

    host = parsed.netloc
    if host.endswith("linkedin.com") and host != "www.linkedin.com":
        host = "www.linkedin.com"
    scheme = parsed.scheme or "https"
    return urlunparse(parsed._replace(netloc=host, scheme=scheme))


def _search_and_select(payload: SearchPayload) -> Tuple[Dict[str, Any], Optional[str], Dict[str, Any]]:
    try:
        search_client = LinkedInSearchClient()
    except ValueError as exc:
        raise RuntimeError(str(exc)) from exc

    try:
        search_result = search_client.search_people(
            payload.first_name,
            payload.last_name,
            search_url=payload.linkedin_url,
        )
    except BrightDataError as exc:
        raise RuntimeError(str(exc)) from exc

    candidates = search_result.get("records", [])
    if not candidates:
        raise RuntimeError("No LinkedIn candidates found for the provided name")

    criteria = _build_search_criteria(payload)
    selected_profile, rationale = select_profile(candidates, criteria)
    return selected_profile, rationale, search_result


def search_and_enrich(payload: SearchPayload) -> Dict[str, Any]:
    cached = get_cached_lookup(payload.first_name, payload.last_name)
    if cached:
        return cached

    selected_profile, rationale, _ = _search_and_select(payload)
    profile_url = selected_profile.get("url")
    if not profile_url:
        raise RuntimeError("Selected profile does not include a LinkedIn URL")

    normalized_url = _normalize_linkedin_profile_url(profile_url)

    try:
        fetcher = LinkedInFetcher()
    except ValueError as exc:
        raise RuntimeError(str(exc)) from exc

    try:
        snapshot = fetcher.fetch_profile(normalized_url)
    except BrightDataError as exc:
        raise RuntimeError(str(exc)) from exc

    records = snapshot.get("records", [])
    if not records:
        raise RuntimeError("LinkedIn snapshot returned no profile records")

    profile_data = records[0]
    crew_outputs = run_networking_crew(profile_data)

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
        "person": person,
        "selector_rationale": rationale,
        "crew_outputs": crew_outputs,
    }

    set_cached_lookup(payload.first_name, payload.last_name, result)
    return result


def process_capture(
    image_bytes: bytes,
    filename: str,
    progress_cb: Optional[Callable[[int, str], None]] = None,
) -> Dict[str, Any]:
    def update(progress: int, message: str) -> None:
        if progress_cb:
            progress_cb(progress, message)

    update(5, "Processing image")
    extracted, markdown = extract_from_bytes(image_bytes, filename)

    basic_info = extracted.get("basic_info", {}) if isinstance(extracted, dict) else {}
    names = basic_info.get("names", "") if isinstance(basic_info, dict) else ""
    if not names:
        raise RuntimeError("Unable to extract names from the image")

    parts = names.split()
    if len(parts) == 1:
        first_name, last_name = parts[0], parts[0]
    else:
        first_name, last_name = parts[0], " ".join(parts[1:])

    additional_context = extracted.get("links", {}) if isinstance(extracted, dict) else {}
    context_parts: List[str] = []
    if isinstance(additional_context, dict):
        for key in ("linkedin", "website", "github"):
            value = additional_context.get(key)
            if value:
                context_parts.append(f"{key}: {value}")
    company = basic_info.get("company") if isinstance(basic_info, dict) else None
    if company:
        context_parts.append(f"company: {company}")

    payload = SearchPayload(
        first_name=first_name,
        last_name=last_name,
        additional_context=", ".join(context_parts) or None,
    )

    update(45, "Searching LinkedIn")
    lookup_result = search_and_enrich(payload)

    combined = {
        "filename": filename,
        "markdown": markdown,
        "extracted": extracted,
    }
    combined.update(lookup_result)

    update(90, "Saving profile")
    stored = save_person_record(combined)
    update(100, "Completed")
    return stored


def generate_chat_reply(message: str, records: List[Dict[str, Any]]) -> str:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    model = os.getenv("CHAT_MODEL", os.getenv("MODEL", "gpt-4o-mini"))

    snippets = []
    for record in records:
        person = record.get("person", {}) or {}
        crew_outputs = record.get("crew_outputs", {}) or {}
        summary_block = crew_outputs.get("summary_generator_task", {}) or {}
        analyzer_block = crew_outputs.get("linkedin_profile_analyzer_task", {}) or {}
        icebreakers = crew_outputs.get("icebreaker_generator_task", {}).get("icebreakers", []) if crew_outputs else []
        extracted = record.get("extracted", {}) or {}
        links = extracted.get("links", {}) if isinstance(extracted, dict) else {}

        snippet_lines = [f"Name: {person.get('name', 'Unknown')}"]
        if person.get("subtitle"):
            snippet_lines.append(f"Subtitle: {person['subtitle']}")
        elif analyzer_block.get("headline"):
            snippet_lines.append(f"Headline: {analyzer_block['headline']}")
        if person.get("location"):
            snippet_lines.append(f"Location: {person['location']}")
        if summary_block.get("summary"):
            snippet_lines.append(f"Summary: {summary_block['summary']}")
        highlights = summary_block.get("key_highlights") or analyzer_block.get("highlights") or []
        if highlights:
            snippet_lines.append("Highlights:")
            snippet_lines.extend(f"- {item}" for item in highlights[:5])
        if icebreakers:
            snippet_lines.append("Icebreakers:")
            snippet_lines.extend(f"- {item.get('category', '')}: {item.get('prompt', '')}" for item in icebreakers[:3])
        if links:
            contact_parts = []
            for field in ("linkedin", "email", "phone"):
                value = links.get(field)
                if value:
                    contact_parts.append(f"{field}: {value}")
            if contact_parts:
                snippet_lines.append("Contact: " + ", ".join(contact_parts))
        snippets.append("\n".join(snippet_lines))

    context = "\n\n".join(snippets)
    system_prompt = (
        "You are a helpful networking assistant. Use only the provided contact information to answer. "
        "Be concise, friendly, and mention specific details when relevant."
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Context about contacts:\n{context}\n\nUser message: {message}",
            },
        ],
        temperature=0.6,
    )

    return (response.choices[0].message.content or "").strip()


def format_person_summary(record: Dict[str, Any]) -> str:
    person = record.get("person", {}) or {}
    crew_outputs = record.get("crew_outputs", {}) or {}
    summary_block = crew_outputs.get("summary_generator_task", {}) or {}
    analyzer_block = crew_outputs.get("linkedin_profile_analyzer_task", {}) or {}

    lines: List[str] = []
    header = person.get("name", "This contact")
    if person.get("subtitle"):
        header += f" — {person['subtitle']}"
    elif analyzer_block.get("headline"):
        header += f" — {analyzer_block['headline']}"
    lines.append(header)

    summary = summary_block.get("summary")
    if summary:
        lines.append(summary)

    highlights = summary_block.get("key_highlights") or analyzer_block.get("highlights") or []
    if highlights:
        lines.append("Key highlights:")
        lines.extend(f"- {item}" for item in highlights[:3])

    return "\n".join(lines)
