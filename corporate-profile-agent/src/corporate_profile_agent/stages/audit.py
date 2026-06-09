"""Stage 5 — Audit layer.

Deterministic, LLM-free validation of extracted claims:

* cross-validation — material claims need >=2 *independent* sources
  (distinct publisher domains), otherwise they're marked accordingly
* authority weighting — regulator filing beats company PDF beats news
* recency — figures older than the latest expected fiscal year get flagged
* sanity — revenue/headcount ratio, currency consistency across financials,
  EBITDA <= revenue, thousands-vs-millions unit errors
* per-field confidence score and an explicit status, so synthesis can keep
  weak data out of the main narrative instead of silently blending it in
"""

from __future__ import annotations

import re
from collections import defaultdict

from ..config import latest_expected_fiscal_year
from ..models import (
    AUTHORITY_WEIGHT,
    AuditedField,
    Claim,
    FieldStatus,
    SourceTier,
)
from .extraction import UNIT_MULTIPLIER

# Rough FX (units per USD) used ONLY for order-of-magnitude sanity checks,
# never for reported figures. Precision is irrelevant here; we are testing
# for 1000x unit errors, not 10% drift.
_FX_PER_USD = {
    "USD": 1.0, "EUR": 0.9,
    "COP": 4000.0, "BRL": 5.0, "MXN": 18.0,
    "CLP": 950.0, "ARS": 1000.0, "PEN": 3.8,
}

# Plausible annual revenue per employee, in USD.
_REV_PER_EMPLOYEE_MIN = 2_000.0
_REV_PER_EMPLOYEE_MAX = 10_000_000.0

_SCALAR_FIELDS = (
    "legal_name", "tax_id", "sector", "description",
    "employees", "revenue", "ebitda", "net_debt",
)
_LIST_FIELDS = (
    "countries_of_operation", "ownership", "executives",
    "recent_results", "announced_plans",
)
_FINANCIAL_FIELDS = ("revenue", "ebitda", "net_debt")


def audit(claims: list[Claim]) -> list[AuditedField]:
    by_field: dict[str, list[Claim]] = defaultdict(list)
    for claim in claims:
        by_field[claim.field].append(claim)

    fields: list[AuditedField] = []
    for name in _SCALAR_FIELDS:
        if by_field.get(name):
            fields.append(_audit_scalar(name, by_field[name]))
    for name in _LIST_FIELDS:
        for group in _group_list_claims(by_field.get(name, [])):
            fields.append(_audit_scalar(name, group))

    _apply_cross_field_sanity(fields)
    return fields


# --------------------------------------------------------------------------

def _norm_text(value: str) -> str:
    return " ".join(re.sub(r"[^\w\s%]", "", value.lower()).split())


def _money_usd(claim: Claim) -> float | None:
    if not isinstance(claim.value, dict):
        return None
    fx = _FX_PER_USD.get((claim.currency or "").upper())
    if fx is None:
        return None
    return (
        claim.value["amount"]
        * UNIT_MULTIPLIER.get(claim.unit or "units", 1.0)
        / fx
    )


def _values_agree(a: Claim, b: Claim) -> bool:
    if isinstance(a.value, (int, float)) and isinstance(b.value, (int, float)):
        hi = max(abs(a.value), abs(b.value))
        return hi == 0 or abs(a.value - b.value) / hi <= 0.02
    if isinstance(a.value, dict) and isinstance(b.value, dict):
        ua, ub = _money_usd(a), _money_usd(b)
        if ua is None or ub is None:
            return _norm_text(a.display) == _norm_text(b.display)
        hi = max(abs(ua), abs(ub))
        return hi == 0 or abs(ua - ub) / hi <= 0.05
    return _norm_text(str(a.display)) == _norm_text(str(b.display))


def _group_list_claims(claims: list[Claim]) -> list[list[Claim]]:
    """Cluster list-field claims (e.g. several executives) by agreement."""
    groups: list[list[Claim]] = []
    for claim in claims:
        for group in groups:
            if _values_agree(group[0], claim):
                group.append(claim)
                break
        else:
            groups.append([claim])
    return groups


def _fiscal_year(as_of: str | None) -> int | None:
    if not as_of:
        return None
    match = re.search(r"(19|20)\d{2}", as_of)
    return int(match.group()) if match else None


def _audit_scalar(name: str, claims: list[Claim]) -> AuditedField:
    notes: list[str] = []

    # Cluster agreeing claims; canonical cluster = best authority, then size.
    clusters = _group_list_claims(claims)
    clusters.sort(key=lambda c: (min(int(x.tier) for x in c), -len(c)))
    canonical = clusters[0]
    canonical.sort(key=lambda c: int(c.tier))
    best = canonical[0]

    conflict = len(clusters) > 1 and name in _SCALAR_FIELDS
    if conflict:
        others = "; ".join(
            f"'{c[0].display}' ({c[0].publisher_domain or c[0].doc_id})"
            for c in clusters[1:]
        )
        notes.append(f"conflicting values from other sources: {others}")

    domains = {c.publisher_domain or c.doc_id for c in canonical}
    independent = len(domains)
    if independent >= 2:
        notes.append(f"corroborated by {independent} independent sources")

    stale = False
    if name in _FINANCIAL_FIELDS:
        year = _fiscal_year(best.as_of)
        expected = latest_expected_fiscal_year()
        if year is not None and year < expected:
            stale = True
            notes.append(
                f"figure is for fiscal year {year}; latest expected is {expected}"
            )

    sanity_fail = _sanity_single(name, best, notes)

    confidence = AUTHORITY_WEIGHT[SourceTier(best.tier)]
    confidence += min(0.15 * (independent - 1), 0.30)
    if conflict:
        confidence -= 0.30
    if stale:
        confidence -= 0.20
    if sanity_fail:
        confidence -= 0.30
    confidence = max(0.0, min(1.0, round(confidence, 2)))

    if conflict or sanity_fail:
        status = FieldStatus.FLAGGED
    elif stale:
        status = FieldStatus.UNVERIFIED
    elif independent >= 2:
        status = FieldStatus.VERIFIED
    elif best.tier == SourceTier.OFFICIAL:
        status = FieldStatus.SINGLE_SOURCE
    else:
        status = FieldStatus.UNVERIFIED
        notes.append("single non-official source")

    return AuditedField(
        field=name, display=best.display, status=status,
        confidence=confidence, supporting_claims=canonical, notes=notes,
    )


def _sanity_single(name: str, claim: Claim, notes: list[str]) -> bool:
    if name not in _FINANCIAL_FIELDS or not isinstance(claim.value, dict):
        return False
    if (claim.currency or "").upper() not in _FX_PER_USD:
        notes.append(f"unrecognized currency '{claim.currency}'")
        return True
    return False


def _apply_cross_field_sanity(fields: list[AuditedField]) -> None:
    by_name = {f.field: f for f in fields if f.field in _SCALAR_FIELDS}

    revenue = by_name.get("revenue")
    ebitda = by_name.get("ebitda")
    employees = by_name.get("employees")

    currencies = {
        (f.supporting_claims[0].currency or "").upper()
        for n, f in by_name.items()
        if n in _FINANCIAL_FIELDS and f.supporting_claims
    }
    if len(currencies) > 1:
        for n in _FINANCIAL_FIELDS:
            if n in by_name:
                _flag(by_name[n],
                      f"currency inconsistency across financials: {sorted(currencies)}")

    rev_usd = _money_usd(revenue.supporting_claims[0]) if revenue and revenue.supporting_claims else None

    if revenue and employees and rev_usd is not None:
        headcount = employees.supporting_claims[0].value
        if isinstance(headcount, (int, float)) and headcount > 0:
            ratio = rev_usd / headcount
            if not (_REV_PER_EMPLOYEE_MIN <= ratio <= _REV_PER_EMPLOYEE_MAX):
                msg = (
                    f"revenue/headcount ratio implausible "
                    f"(~{ratio:,.0f} USD per employee) — possible "
                    "thousands-vs-millions unit error"
                )
                _flag(revenue, msg)
                _flag(employees, msg)

    if revenue and ebitda and rev_usd is not None:
        ebitda_usd = _money_usd(ebitda.supporting_claims[0]) if ebitda.supporting_claims else None
        if ebitda_usd is not None and ebitda_usd > rev_usd * 1.05:
            _flag(ebitda, "EBITDA exceeds revenue — possible unit or extraction error")


def _flag(field: AuditedField, note: str) -> None:
    if note not in field.notes:
        field.notes.append(note)
    field.status = FieldStatus.FLAGGED
    field.confidence = max(0.0, round(field.confidence - 0.30, 2))
