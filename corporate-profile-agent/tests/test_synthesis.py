from corporate_profile_agent.models import (
    AuditedField,
    AuditedProfile,
    Claim,
    EntityRef,
    FieldStatus,
    SourceDocument,
    SourceTier,
)
from corporate_profile_agent.stages.synthesis import render


def make_field(name, display, status, confidence=0.9):
    return AuditedField(
        field=name, display=display, status=status, confidence=confidence,
        supporting_claims=[Claim(
            field=name, value=display, display=display, doc_id="abc123",
            tier=SourceTier.OFFICIAL, page=3, quote="...",
        )],
        notes=["corroborated by 2 independent sources"]
        if status == FieldStatus.VERIFIED else ["single non-official source"],
    )


def make_profile():
    return AuditedProfile(
        entity=EntityRef(
            input_name="Ecopetrol", country="CO", tax_id="899999068-1",
            tax_id_type="NIT", resolved=True,
            resolution_notes="anchored to supplied, checksum-valid ID",
        ),
        fields=[
            make_field("legal_name", "ECOPETROL S.A.", FieldStatus.VERIFIED),
            make_field("sector", "Oil & Gas", FieldStatus.VERIFIED),
            make_field("revenue", "133,000.0 billions COP (FY2025)",
                       FieldStatus.SINGLE_SOURCE),
            make_field("employees", "18,000", FieldStatus.UNVERIFIED, 0.4),
            make_field("ebitda", "999,999.0 millions COP (FY2025)",
                       FieldStatus.FLAGGED, 0.2),
        ],
        documents=[SourceDocument(
            doc_id="abc123", url="https://www.rues.org.co/?nit=899999068",
            tier=SourceTier.OFFICIAL, title="RUES registry record",
            sha256="f" * 64,
        )],
    )


def test_verified_data_in_narrative():
    report = render(make_profile())
    assert "# ECOPETROL S.A." in report
    assert "Oil & Gas" in report
    assert "133,000.0 billions COP" in report


def test_weak_data_excluded_from_scale_section():
    report = render(make_profile())
    scale = report.split("## Scale")[1].split("##")[0]
    # Unverified employees and flagged EBITDA must not appear in the narrative.
    assert "18,000" not in scale
    assert "999,999.0" not in scale


def test_weak_data_listed_explicitly():
    report = render(make_profile())
    assert "## Unverified & flagged data" in report
    section = report.split("## Unverified & flagged data")[1].split("## Sources")[0]
    assert "18,000" in section
    assert "999,999.0" in section


def test_sources_table_has_traceability():
    report = render(make_profile())
    assert "rues.org.co" in report
    assert "ffffffffffff" in report  # sha prefix
    assert "| ID | Tier | Title | URL | Retrieved | SHA-256 |" in report


def test_confidence_notes_per_field():
    report = render(make_profile())
    assert "## Confidence notes" in report
    assert "abc123 p.3" in report


def test_data_gaps_reported():
    report = render(make_profile())
    gaps = report.split("## Risks & data gaps")[1].split("##")[0]
    assert "executives" in gaps and "ownership" in gaps


def test_unresolved_entity_renders_without_crashing():
    profile = AuditedProfile(entity=EntityRef(
        input_name="Acme", country="CO",
        resolution_notes="ambiguous — 4 registry candidates",
    ))
    report = render(profile)
    assert "unresolved" in report
    assert "ambiguous" in report
