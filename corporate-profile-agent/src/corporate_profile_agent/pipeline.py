"""Pipeline orchestrator: intake -> discovery -> acquisition -> extraction
-> audit -> synthesis."""

from __future__ import annotations

import logging
from pathlib import Path

from .config import DATA_DIR
from .models import AuditedProfile
from .stages import acquisition, audit, discovery, extraction, intake, synthesis

log = logging.getLogger(__name__)


def run(
    name: str,
    country: str,
    tax_id: str | None = None,
    data_dir: Path | None = None,
    max_sources: int = 12,
) -> tuple[AuditedProfile, str]:
    """Run the full pipeline. Returns (audited profile, markdown report)."""
    # 1. Intake & entity resolution
    entity = intake.resolve(name, country, tax_id)
    log.info("intake: %s", entity.resolution_notes)
    if not entity.resolved:
        profile = AuditedProfile(entity=entity)
        return profile, synthesis.render(profile)

    out_dir = (data_dir or DATA_DIR) / entity.tax_id.replace("/", "_")

    # 2. Source discovery (tiered)
    sources = discovery.discover(name, country, entity.tax_id, max_sources)
    log.info("discovery: %d candidate sources", len(sources))

    # 3. Document acquisition (download + hash + parse/OCR)
    documents = acquisition.acquire(sources, out_dir / "docs")
    log.info("acquisition: %d documents stored", len(documents))

    # 4. Extraction into the fixed schema (per document, with citations)
    entity_desc = f"{name} ({country}, {entity.tax_id_type} {entity.tax_id})"
    claims = extraction.extract_all(documents, entity_desc)
    log.info("extraction: %d claims", len(claims))

    # 5. Audit (cross-validation, authority, recency, sanity, confidence)
    fields = audit.audit(claims)

    # 6. Synthesis from the validated schema only
    profile = AuditedProfile(
        entity=entity, fields=fields, documents=[d.meta for d in documents]
    )
    report = synthesis.render(profile)

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "profile.json").write_text(
        profile.model_dump_json(indent=2), encoding="utf-8"
    )
    (out_dir / "profile.md").write_text(report, encoding="utf-8")
    log.info("wrote %s", out_dir / "profile.md")
    return profile, report
