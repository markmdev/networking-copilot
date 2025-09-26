"""Helpers for extracting structured data from images using Agentic Doc + OpenAI."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Tuple

from agentic_doc.parse import parse
from openai import OpenAI

EXTRACTION_TEMPLATE = """
Extract the following information from this content and return as JSON:
- basic_info: names, company
- links: linkedin, github, website, email, phone
- image: path to the image file

Content: {content}

Return only valid JSON format:
{{
  "basic_info": {{
    "names": "extracted names",
    "company": "extracted company"
  }},
  "links": {{
    "linkedin": "linkedin url if found",
    "github": "github url if found",
    "website": "website url if found",
    "email": "email if found",
    "phone": "phone if found"
  }},
  "image": "{image_name}"
}}
"""


def _load_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    return OpenAI(api_key=api_key)


def extract_from_image(image_path: str) -> Tuple[Dict[str, Any], str]:
    """Parse the image and extract structured data.

    Returns a tuple of (extracted_json, markdown_content).
    """

    results = parse(image_path)
    if not results:
        raise ValueError("No content returned from Agentic Doc parser")

    first = results[0]
    markdown = getattr(first, "markdown", "").strip()
    if not markdown:
        raise ValueError("Agentic Doc parser returned empty markdown content")

    image_name = Path(image_path).name
    prompt = EXTRACTION_TEMPLATE.format(content=markdown, image_name=image_name)

    client = _load_client()
    model = os.getenv("MODEL", "gpt-4o-mini")

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are an extraction assistant. Respond with valid JSON only.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,
    )

    content = response.choices[0].message.content or ""

    try:
        extracted = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"OpenAI response was not valid JSON: {content}") from exc

    return extracted, markdown
