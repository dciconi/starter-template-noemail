"""Stage 1 — Intake & entity resolution.

Normalizes the input and anchors it to the official tax/registry ID. If the
caller supplies an ID, we validate its checksum. If not, we ask the country's
registry adapter to resolve the name to candidates; ambiguity (homonyms,
holding structures) is surfaced rather than silently picked through.
"""

from __future__ import annotations

import unicodedata

from .. import tax_ids
from ..models import EntityRef
from ..registries import get_registry

# Legal-form suffixes stripped for matching, not for display.
_LEGAL_FORMS = (
    "s.a.s", "sas", "s.a.", "sa", "s.a", "ltda", "ltda.", "spa", "s.p.a",
    "s.r.l", "srl", "e.s.p", "esp", "s.a.b. de c.v.", "s.a. de c.v.",
    "c.a.", "eirl", "s.a.a",
)


def normalize_name(name: str) -> str:
    """Lowercase, strip accents and legal-form suffixes for fuzzy matching."""
    text = unicodedata.normalize("NFKD", name)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = " ".join(text.lower().split())
    for form in sorted(_LEGAL_FORMS, key=len, reverse=True):
        if text.endswith(" " + form):
            text = text[: -len(form) - 1]
            break
    return text.strip(" .,")


def resolve(name: str, country: str, tax_id: str | None = None) -> EntityRef:
    entity = EntityRef(input_name=name, country=country.upper())

    if tax_id:
        result = tax_ids.validate(country, tax_id)
        if not result.valid:
            entity.resolution_notes = (
                f"supplied {result.id_type} failed validation: {result.reason}"
            )
            return entity
        entity.tax_id = result.normalized
        entity.tax_id_type = result.id_type
        entity.resolved = True
        entity.resolution_notes = "anchored to supplied, checksum-valid ID"
        return entity

    registry = get_registry(country)
    if registry is None:
        entity.resolution_notes = (
            f"no registry adapter for {country}; supply a tax ID explicitly"
        )
        return entity

    candidates = registry.search_by_name(normalize_name(name))
    if not candidates:
        entity.resolution_notes = "registry search returned no candidates"
        return entity
    if len(candidates) > 1:
        listing = "; ".join(f"{c.name} [{c.tax_id}]" for c in candidates[:5])
        entity.resolution_notes = (
            f"ambiguous — {len(candidates)} registry candidates: {listing}. "
            "Re-run with an explicit tax ID."
        )
        return entity

    match = candidates[0]
    result = tax_ids.validate(country, match.tax_id)
    entity.tax_id = result.normalized if result.valid else match.tax_id
    entity.tax_id_type = result.id_type
    entity.resolved = result.valid
    entity.resolution_notes = (
        f"resolved via {registry.name} to '{match.name}'"
        + ("" if result.valid else " (registry ID failed checksum — review)")
    )
    return entity
