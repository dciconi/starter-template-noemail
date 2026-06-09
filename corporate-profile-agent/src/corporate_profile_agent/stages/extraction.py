"""Stage 4 — Extraction into the fixed schema.

One structured-output call per document (not one giant call over everything):
per-document extraction keeps each claim's provenance unambiguous and lets
the audit layer cross-validate *across* documents. Native PDFs go to the
model as document blocks so page citations line up with the actual file;
extracted text is the fallback for OCR'd or HTML sources.

Every value carries a citation (page + verbatim quote). The extractor is
instructed never to infer values absent from the document.
"""

from __future__ import annotations

import base64
import logging
from pathlib import Path

from ..config import EXTRACTION_MODEL, get_client
from ..models import Claim, DocMoney, DocumentExtraction
from .acquisition import AcquiredDocument

log = logging.getLogger(__name__)

_SYSTEM = """\
You extract structured facts about one specific company from one source
document, for a verified corporate profile of a Latin American company.

Rules — these are load-bearing for a downstream audit step:
- Extract ONLY facts stated in this document. Never infer, estimate, or use
  outside knowledge. A field not stated in the document stays null/empty.
- Every value needs a citation: the page number (if paged) and a verbatim
  quote of at most 300 characters that contains the value.
- Confirm the document refers to the target company (matching tax ID or
  unambiguous legal name). If it refers to a different company, return all
  fields null/empty.
- Financial figures: record the amount exactly as printed plus the printed
  scale (thousands/millions/billions) and currency. Spanish/Portuguese
  filings often state "cifras en miles de pesos" once in a header — apply it.
- Dates/periods: record the fiscal period each figure refers to (e.g. FY2025).
"""

_MAX_DOC_CHARS = 400_000  # ~100K tokens of extracted text; truncate beyond


def extract_all(documents: list[AcquiredDocument], entity_desc: str) -> list[Claim]:
    claims: list[Claim] = []
    for doc in documents:
        try:
            extraction = extract_one(doc, entity_desc)
        except Exception as exc:
            log.warning("extraction failed for %s: %s", doc.meta.doc_id, exc)
            continue
        if extraction is not None:
            claims.extend(_to_claims(extraction, doc))
    return claims


def extract_one(doc: AcquiredDocument, entity_desc: str) -> DocumentExtraction | None:
    client = get_client()
    if client is None:
        log.warning("ANTHROPIC_API_KEY not set — skipping extraction")
        return None

    instruction = (
        f"Target company: {entity_desc}\n"
        f"Source: {doc.meta.title or doc.meta.url} "
        f"(authority tier {int(doc.meta.tier)}, retrieved {doc.meta.retrieved_at:%Y-%m-%d})\n"
        "Extract the profile fields from this document."
    )

    content: list[dict] = []
    if doc.meta.content_type.endswith("pdf") and not doc.meta.ocr_applied:
        pdf_bytes = Path(doc.meta.local_path).read_bytes()
        content.append({
            "type": "document",
            "source": {
                "type": "base64",
                "media_type": "application/pdf",
                "data": base64.standard_b64encode(pdf_bytes).decode(),
            },
        })
    else:
        text = doc.text[:_MAX_DOC_CHARS]
        if not text.strip():
            return None
        content.append({"type": "text", "text": text})
    content.append({"type": "text", "text": instruction})

    response = client.messages.parse(
        model=EXTRACTION_MODEL,
        max_tokens=16000,
        thinking={"type": "adaptive"},
        system=_SYSTEM,
        output_format=DocumentExtraction,
        messages=[{"role": "user", "content": content}],
    )
    return response.parsed_output


def _to_claims(ext: DocumentExtraction, doc: AcquiredDocument) -> list[Claim]:
    meta = doc.meta
    claims: list[Claim] = []

    def add(field: str, value, display: str, citation, as_of=None,
            currency=None, unit=None):
        claims.append(Claim(
            field=field, value=value, display=display,
            doc_id=meta.doc_id, tier=meta.tier,
            publisher_domain=meta.publisher_domain,
            page=citation.page, quote=citation.quote,
            as_of=as_of, currency=currency, unit=unit,
        ))

    for name in ("legal_name", "tax_id", "sector", "description"):
        item = getattr(ext, name)
        if item:
            add(name, item.value, item.value, item.citation, item.as_of)

    for item in ext.countries_of_operation:
        add("countries_of_operation", item.value, item.value, item.citation, item.as_of)
    for owner in ext.ownership:
        display = owner.name + (
            f" ({owner.stake_pct:g}%)" if owner.stake_pct is not None else ""
        )
        add("ownership", owner.model_dump(), display, owner.citation)
    for execu in ext.executives:
        add("executives", execu.model_dump(), f"{execu.name} — {execu.role}",
            execu.citation)
    if ext.employees:
        add("employees", ext.employees.value, f"{ext.employees.value:,.0f}",
            ext.employees.citation, ext.employees.as_of)

    for name in ("revenue", "ebitda", "net_debt"):
        money: DocMoney | None = getattr(ext, name)
        if money:
            add(name, money.model_dump(),
                f"{money.amount:,.1f} {money.unit} {money.currency} ({money.fiscal_period})",
                money.citation, money.fiscal_period, money.currency, money.unit)

    for item in ext.recent_results:
        add("recent_results", item.value, item.value, item.citation, item.as_of)
    for item in ext.announced_plans:
        add("announced_plans", item.value, item.value, item.citation, item.as_of)

    return claims


# Scale multipliers shared with the audit layer's sanity checks.
UNIT_MULTIPLIER = {
    "units": 1.0,
    "thousands": 1e3,
    "millions": 1e6,
    "billions": 1e9,
}
