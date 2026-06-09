"""Fixed schema for the pipeline.

Three layers of models:

1. Wire models (``Doc*``) — what the LLM fills in per document, with a
   citation on every value. These are also the structured-output schema.
2. Claims — per-document extracted values flattened into a uniform shape the
   audit layer can cross-validate.
3. Audited profile — the validated schema the synthesis stage renders from.
   Synthesis never sees raw search text or raw document text.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum, IntEnum
from typing import Literal, Optional

from pydantic import BaseModel, Field


# --------------------------------------------------------------------------
# Sources
# --------------------------------------------------------------------------

class SourceTier(IntEnum):
    """Authority tiers. Lower number = higher authority."""

    OFFICIAL = 1    # corporate registries, regulators (RUES, CMF, CVM, ...)
    PRIMARY = 2     # the company itself: annual reports, IR PDFs, site
    SECONDARY = 3   # news, industry reports, LinkedIn, job postings


AUTHORITY_WEIGHT = {
    SourceTier.OFFICIAL: 1.0,
    SourceTier.PRIMARY: 0.7,
    SourceTier.SECONDARY: 0.4,
}


class SourceDocument(BaseModel):
    doc_id: str                      # short stable id, e.g. sha256[:12]
    url: str
    tier: SourceTier
    title: str = ""
    content_type: str = ""
    sha256: str = ""
    retrieved_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    local_path: str = ""
    publisher_domain: str = ""       # used for source-independence checks
    ocr_applied: bool = False


# --------------------------------------------------------------------------
# Wire models: per-document LLM extraction (structured output schema)
# --------------------------------------------------------------------------

class DocCitation(BaseModel):
    page: Optional[int] = Field(
        None, description="1-based page number in the source document, if paged."
    )
    quote: str = Field(
        description="Verbatim quote (<=300 chars) supporting the value."
    )


class DocText(BaseModel):
    value: str
    as_of: Optional[str] = Field(
        None, description="Date or fiscal period the statement refers to, e.g. 'FY2025' or '2026-03'."
    )
    citation: DocCitation


class DocNumber(BaseModel):
    value: float
    as_of: Optional[str] = None
    citation: DocCitation


class DocMoney(BaseModel):
    amount: float = Field(description="Numeric amount exactly as printed, before unit scaling.")
    currency: str = Field(description="ISO 4217 code, e.g. COP, BRL, USD.")
    unit: Literal["units", "thousands", "millions", "billions"] = Field(
        description="Scale the printed amount is expressed in."
    )
    fiscal_period: str = Field(description="e.g. 'FY2025', 'H1 2026', 'Q1 2026'.")
    citation: DocCitation


class DocOwner(BaseModel):
    name: str
    stake_pct: Optional[float] = None
    citation: DocCitation


class DocExecutive(BaseModel):
    name: str
    role: str
    citation: DocCitation


class DocumentExtraction(BaseModel):
    """Everything extractable from one source document. Null = not stated.

    The extractor must never infer values not present in the document.
    """

    legal_name: Optional[DocText] = None
    tax_id: Optional[DocText] = None
    sector: Optional[DocText] = None
    description: Optional[DocText] = None
    countries_of_operation: list[DocText] = Field(default_factory=list)
    ownership: list[DocOwner] = Field(default_factory=list)
    executives: list[DocExecutive] = Field(default_factory=list)
    employees: Optional[DocNumber] = None
    revenue: Optional[DocMoney] = None
    ebitda: Optional[DocMoney] = None
    net_debt: Optional[DocMoney] = None
    recent_results: list[DocText] = Field(default_factory=list)
    announced_plans: list[DocText] = Field(default_factory=list)


# --------------------------------------------------------------------------
# Claims: flattened extraction output the audit layer consumes
# --------------------------------------------------------------------------

class Claim(BaseModel):
    field: str                       # e.g. "revenue", "employees"
    value: object                    # str | float | DocMoney dump
    display: str                     # human-readable rendering of value
    doc_id: str
    tier: SourceTier
    publisher_domain: str = ""
    page: Optional[int] = None
    quote: str = ""
    as_of: Optional[str] = None
    currency: Optional[str] = None
    unit: Optional[str] = None


# --------------------------------------------------------------------------
# Audited profile: what synthesis renders from
# --------------------------------------------------------------------------

class FieldStatus(str, Enum):
    VERIFIED = "verified"            # >=2 independent sources, no flags
    SINGLE_SOURCE = "single_source"  # 1 source, official tier, no flags
    FLAGGED = "flagged"              # conflicts or failed sanity checks
    UNVERIFIED = "unverified"        # 1 non-official source or stale data


class AuditedField(BaseModel):
    field: str
    display: str                     # canonical (highest-authority) value
    status: FieldStatus
    confidence: float                # 0..1
    supporting_claims: list[Claim] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class EntityRef(BaseModel):
    input_name: str
    country: str
    tax_id: str = ""                 # normalized official ID; "" if unresolved
    tax_id_type: str = ""
    resolved: bool = False
    resolution_notes: str = ""


class AuditedProfile(BaseModel):
    entity: EntityRef
    fields: list[AuditedField] = Field(default_factory=list)
    documents: list[SourceDocument] = Field(default_factory=list)
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def get(self, name: str) -> Optional[AuditedField]:
        for f in self.fields:
            if f.field == name:
                return f
        return None
