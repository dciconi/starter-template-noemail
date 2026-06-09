"""Stage 2 — Source discovery, tiered by authority.

Tier 1 comes straight from the country's registry adapter (deterministic
URLs keyed off the tax ID — no search involved). Tiers 2 and 3 use Claude
with the server-side web_search tool to find the company's own IR material
and secondary coverage, returning candidate URLs as structured output.
"""

from __future__ import annotations

import logging
from typing import Optional

from pydantic import BaseModel, Field

from ..config import EXTRACTION_MODEL, get_client
from ..models import SourceTier
from ..registries import get_registry

log = logging.getLogger(__name__)


class CandidateSource(BaseModel):
    url: str
    title: str
    tier: int = Field(description="2 = company's own material, 3 = secondary coverage.")
    rationale: str = Field(description="Why this source is useful for the profile.")
    is_pdf: bool = Field(description="True if the URL points at a PDF document.")


class DiscoveryResult(BaseModel):
    sources: list[CandidateSource] = Field(default_factory=list)


def discover(entity_name: str, country: str, tax_id: str, max_sources: int = 12) -> list[dict]:
    """Return source candidates as dicts: url, title, tier, kind."""
    found: list[dict] = []

    registry = get_registry(country)
    if registry is not None and tax_id:
        for src in registry.official_sources(tax_id):
            found.append(
                {"url": src.url, "title": src.title,
                 "tier": SourceTier.OFFICIAL, "kind": src.kind}
            )

    web = _discover_web(entity_name, country, tax_id, max_sources - len(found))
    found.extend(web)
    return found


_DISCOVERY_PROMPT = """\
Find sources to build a verified corporate profile of this Latin American company:

  Company: {name}
  Country: {country}
  Official tax/registry ID: {tax_id}

Search for, in priority order:
1. The company's investor-relations page and latest annual report / financial
   statements PDF (tier 2).
2. The company's official website "about" page and recent press releases (tier 2).
3. Recent reputable news coverage of results, ownership changes, or announced
   plans, plus hiring/headcount signals (tier 3).

Confirm each source actually refers to the company with this exact tax ID —
homonyms are common. Prefer PDFs of filed financial statements over web pages.
Return at most {limit} sources."""


def _discover_web(name: str, country: str, tax_id: str, limit: int) -> list[dict]:
    if limit <= 0:
        return []
    client = get_client()
    if client is None:
        log.warning("ANTHROPIC_API_KEY not set — skipping tier 2/3 web discovery")
        return []
    try:
        response = client.messages.parse(
            model=EXTRACTION_MODEL,
            max_tokens=16000,
            thinking={"type": "adaptive"},
            tools=[{"type": "web_search_20260209", "name": "web_search"}],
            output_format=DiscoveryResult,
            messages=[{
                "role": "user",
                "content": _DISCOVERY_PROMPT.format(
                    name=name, country=country, tax_id=tax_id, limit=limit
                ),
            }],
        )
    except Exception as exc:
        log.warning("web discovery failed: %s", exc)
        return []

    result: Optional[DiscoveryResult] = response.parsed_output
    if result is None:
        return []
    return [
        {
            "url": s.url,
            "title": s.title,
            "tier": SourceTier.PRIMARY if s.tier <= 2 else SourceTier.SECONDARY,
            "kind": "pdf" if s.is_pdf else "page",
        }
        for s in result.sources[:limit]
    ]
