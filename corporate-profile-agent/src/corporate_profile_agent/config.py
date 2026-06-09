"""Shared configuration and the Anthropic client singleton."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

EXTRACTION_MODEL = os.environ.get("CPA_MODEL", "claude-opus-4-8")
DATA_DIR = Path(os.environ.get("CPA_DATA_DIR", "data"))

# Latest fiscal year we consider "current"; figures older than this get a
# recency flag in the audit layer.
def latest_expected_fiscal_year() -> int:
    from datetime import date

    return date.today().year - 1


@lru_cache(maxsize=1)
def get_client():
    """Return an Anthropic client, or None when no credentials are present
    (keeps the deterministic stages and tests runnable offline)."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    from anthropic import Anthropic

    return Anthropic()
