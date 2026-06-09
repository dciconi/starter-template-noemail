"""Stage 6 — Synthesis.

Generates the markdown report from the *audited* schema only — never from
raw search text or document text. Fields that failed the audit (flagged or
unverified) are excluded from the main narrative and listed in an explicit
"Unverified & flagged" section instead of being silently blended in.

Structure: what they do -> scale -> ownership & governance -> recent
performance -> strategy/announced plans -> risks and data gaps, then a
sources table and per-field confidence notes.
"""

from __future__ import annotations

from ..models import AuditedProfile, FieldStatus

_TRUSTED = {FieldStatus.VERIFIED, FieldStatus.SINGLE_SOURCE}

_STATUS_LABEL = {
    FieldStatus.VERIFIED: "verified (>=2 independent sources)",
    FieldStatus.SINGLE_SOURCE: "single official source",
    FieldStatus.FLAGGED: "FLAGGED",
    FieldStatus.UNVERIFIED: "unverified",
}


def render(profile: AuditedProfile) -> str:
    entity = profile.entity
    lines: list[str] = []
    add = lines.append

    title = _trusted_display(profile, "legal_name") or entity.input_name
    add(f"# {title}")
    add("")
    add(f"**Country:** {entity.country}  ")
    add(f"**{entity.tax_id_type or 'Tax ID'}:** {entity.tax_id or 'unresolved'}  ")
    add(f"**Generated:** {profile.generated_at:%Y-%m-%d}  ")
    add(f"**Entity resolution:** {entity.resolution_notes}")
    add("")

    add("## What they do")
    sector = _trusted_display(profile, "sector")
    description = _trusted_display(profile, "description")
    geo = _trusted_list(profile, "countries_of_operation")
    if description:
        add(description)
    if sector:
        add(f"\n**Sector:** {sector}")
    if geo:
        add(f"**Geography of operations:** {', '.join(geo)}")
    if not (description or sector or geo):
        add("_No verified data._")
    add("")

    add("## Scale")
    rows = []
    for name, label in (("revenue", "Revenue"), ("ebitda", "EBITDA"),
                        ("net_debt", "Net debt"), ("employees", "Employees")):
        field = profile.get(name)
        if field and field.status in _TRUSTED:
            rows.append(f"- **{label}:** {field.display} "
                        f"(confidence {field.confidence:.2f})")
    lines.extend(rows or ["_No verified data._"])
    add("")

    add("## Ownership & governance")
    owners = _trusted_list(profile, "ownership")
    execs = _trusted_list(profile, "executives")
    if owners:
        add("**Ownership:**")
        lines.extend(f"- {o}" for o in owners)
    if execs:
        add("**Key executives:**")
        lines.extend(f"- {e}" for e in execs)
    if not (owners or execs):
        add("_No verified data._")
    add("")

    add("## Recent performance")
    results = _trusted_list(profile, "recent_results")
    if results:
        lines.extend(f"- {r}" for r in results)
    else:
        add("_No verified data._")
    add("")

    add("## Strategy & announced plans")
    plans = _trusted_list(profile, "announced_plans")
    if plans:
        lines.extend(f"- {p}" for p in plans)
    else:
        add("_No verified data._")
    add("")

    add("## Risks & data gaps")
    weak = [f for f in profile.fields if f.status not in _TRUSTED]
    missing = _missing_fields(profile)
    if not weak and not missing:
        add("_None identified._")
    if missing:
        add(f"- No data found for: {', '.join(missing)}")
    for field in weak:
        add(f"- **{field.field}** is {_STATUS_LABEL[field.status]}: "
            + ("; ".join(field.notes) or "insufficient sourcing"))
    add("")

    if weak:
        add("## Unverified & flagged data (excluded from the profile above)")
        for field in weak:
            add(f"- **{field.field}:** {field.display} — "
                f"{_STATUS_LABEL[field.status]}, confidence {field.confidence:.2f}")
        add("")

    add("## Sources")
    add("| ID | Tier | Title | URL | Retrieved | SHA-256 |")
    add("|---|---|---|---|---|---|")
    for doc in profile.documents:
        add(f"| {doc.doc_id} | {int(doc.tier)} | {doc.title or '—'} "
            f"| {doc.url} | {doc.retrieved_at:%Y-%m-%d} | {doc.sha256[:12]}… |")
    add("")

    add("## Confidence notes")
    add("| Field | Value | Status | Confidence | Citations |")
    add("|---|---|---|---|---|")
    for field in profile.fields:
        cites = "; ".join(
            f"{c.doc_id}" + (f" p.{c.page}" if c.page else "")
            for c in field.supporting_claims
        )
        add(f"| {field.field} | {field.display} | {field.status.value} "
            f"| {field.confidence:.2f} | {cites} |")
    add("")

    return "\n".join(lines)


def _trusted_display(profile: AuditedProfile, name: str) -> str | None:
    field = profile.get(name)
    return field.display if field and field.status in _TRUSTED else None


def _trusted_list(profile: AuditedProfile, name: str) -> list[str]:
    return [
        f.display for f in profile.fields
        if f.field == name and f.status in _TRUSTED
    ]


def _missing_fields(profile: AuditedProfile) -> list[str]:
    expected = {"legal_name", "sector", "revenue", "ebitda", "employees",
                "ownership", "executives"}
    present = {f.field for f in profile.fields}
    return sorted(expected - present)
