# Networking Copilot API Reference

This document describes the HTTP endpoints exposed by the Networking Copilot backend so the UI can integrate search, profile enrichment, and crew outputs.

## Overview

- **Base URL (local dev)**: `http://127.0.0.1:8000`
- **Run server**: `uv run uvicorn networking.api:app --reload`
- **Authentication**: none
- **Content type**: JSON requests/responses
- **Environment variables** (required before starting the server):
  - `BRIGHTDATA_API_KEY`
  - `BRIGHTDATA_DATASET_ID` (profile snapshot dataset `gd_l1viktl72bvl7bjuj0`)
  - `BRIGHTDATA_SEARCH_DATASET_ID` (people search dataset `gd_m8d03he47z8nwb5xc`)
  - `OPENAI_API_KEY` and `MODEL` for CrewAI agents

All endpoints return standard FastAPI error payloads on failures, e.g. `{ "detail": "message" }` with appropriate HTTP status codes.

## GET /health

Simple readiness probe.

**Response** `200 OK`
```json
{ "status": "ok" }
```

## POST /search

Search LinkedIn via Bright Data, select the best matching candidate, and return lightweight profile info plus the selector’s rationale. Useful when the UI needs to display options before running the full crew.

**Request body**
```json
{
  "first_name": "Tony",
  "last_name": "Kipkemboi",
  "additional_context": "Tech PM in San Francisco",   // optional
  "linkedin_url": "https://www.linkedin.com"          // optional override of search site
}
```

**Response** `200 OK`
```json
{
  "selected_profile": {
    "url": "https://www.linkedin.com/in/example",
    "name": "Example Person",
    "subtitle": "Product Manager at Example",
    "location": "San Francisco Bay Area",
    "experience": "Example Corp, +2 more",
    "education": "Example University",
    "avatar": "https://..."
  },
  "selector_rationale": "Explanation of why this candidate was chosen."
}
```

**Error codes**
- `404` – no candidates returned for the given name
- `502` – Bright Data errors or selector failure

## POST /lookup

End-to-end flow: search, select best match, fetch full LinkedIn profile snapshot, and run the Networking crew (analyzer, summary, icebreakers). UI can use this to show actionable insights for the confirmed person.

**Request body**: same as `/search`.

**Response** `200 OK`
```json
{
  "person": {
    "url": "https://www.linkedin.com/in/example",
    "name": "Example Person",
    "subtitle": "Product Manager at Example",
    "location": "San Francisco Bay Area",
    "experience": "Example Corp, +2 more",
    "education": "Example University",
    "avatar": "https://..."
  },
  "selector_rationale": "Explanation of the selection.",
  "crew_outputs": {
    "linkedin_profile_analyzer_task": {
      "profile_name": "Example Person",
      "headline": "Product Manager at Example",
      "current_title": "Product Manager",
      "current_company": "Example",
      "location": "San Francisco Bay Area",
      "highlights": [
        "Exactly 10 bullet points summarizing the profile"
      ]
    },
    "summary_generator_task": {
      "summary": "Two-sentence professional summary.",
      "key_highlights": ["Highlight 1", "Highlight 2", "Highlight 3"]
    },
    "icebreaker_generator_task": {
      "icebreakers": [
        { "category": "professional", "prompt": "..." },
        { "category": "educational", "prompt": "..." },
        { "category": "industry", "prompt": "..." }
      ]
    }
  }
}
```

**Error codes**
- Same as `/search`
- `502` – Bright Data profile fetch failure
- `500` – Crew execution error

## POST /linkedin

Fetch a single LinkedIn profile snapshot via Bright Data. Useful when the UI already knows the profile URL.

**Request body**
```json
{ "url": "https://www.linkedin.com/in/example" }
```

**Response** `200 OK`
```json
{
  "snapshot_id": "sd_xxx",
  "dataset_id": "gd_l1viktl72bvl7bjuj0",
  "status": "ready",
  "errors": 0,
  "records": [
    {
      "id": "example",
      "name": "Example Person",
      "city": "San Francisco Bay Area",
      "country_code": "US",
      "position": "Product Manager",
      "about": "...",
      "current_company": { ... },
      "experience": [ ... ],
      "education": [ ... ],
      "certifications": [ ... ],
      "projects": [ ... ],
      "organizations": [ ... ],
      "first_name": "Example",
      "last_name": "Person",
      "timestamp": "2025-09-26T21:00:00.000Z",
      "input": { "url": "https://www.linkedin.com/in/example" },
      "error": null,
      "warning": null
    }
  ]
}
```

**Error codes**
- `422` – invalid URL format
- `502` – Bright Data error

## POST /run

Kick off the Networking crew directly with a LinkedIn profile payload (e.g., cached snapshot). This bypasses Bright Data calls and is useful for testing or batch runs.

**Request body**
```json
{
  "linkedin_data": {
    "id": "example",
    "name": "Example Person",
    "headline": "Product Manager at Example",
    ...
  }
}
```
You may also send an array of profile objects; the crew will use the first entry.

**Response** `200 OK`
```json
{
  "linkedin_profile_analyzer_task": { ... },
  "summary_generator_task": { ... },
  "icebreaker_generator_task": { ... }
}
```

**Error codes**
- `422` – missing or invalid payload
- `500` – crew execution error

## Error Handling Summary

- `422 Unprocessable Entity` – validation issues (e.g., invalid URL)
- `404 Not Found` – no candidates found in `/search`
- `500 Internal Server Error` – unexpected crew/runtime failure
- `502 Bad Gateway` – Bright Data API errors or selection failures

The `detail` field in error responses contains a human-readable message for display or logging.

## Example Integrations

### Search then Lookup Flow
1. UI calls `/search` to get the best candidate and show confirmation to the user.
2. After confirmation, UI calls `/lookup` to fetch the full profile insights and display analyzer/summary/icebreaker results.

### Direct Lookup Flow
- If the UI already has enough context, call `/lookup` directly. The response includes both the core person card (`person`) and conversation-ready content under `crew_outputs`.

### Direct Profile Fetch
- To display raw LinkedIn data without crew processing, call `/linkedin` and use the first entry in `records`.

## Notes for UI Developers

- All responses are JSON; no pagination is used.
- `crew_outputs` keys correspond to task identifiers defined in the CrewAI configuration. Each task returns the schema documented above.
- `selector_rationale` explains why the chosen candidate was favored. Displaying it can help users understand automatic decisions.
- Bright Data calls may take several seconds; consider showing loading states for `/search`, `/lookup`, and `/linkedin`.
- If Bright Data returns localized profile URLs (e.g., `ke.linkedin.com`), the backend normalizes them to `www.linkedin.com` before fetching the full profile.

For further questions or new endpoint requirements, coordinate with the backend team to keep this document up-to-date.
