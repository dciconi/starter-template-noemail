from corporate_profile_agent.config import latest_expected_fiscal_year
from corporate_profile_agent.models import Claim, FieldStatus, SourceTier
from corporate_profile_agent.stages.audit import audit

FY = f"FY{latest_expected_fiscal_year()}"
OLD_FY = f"FY{latest_expected_fiscal_year() - 2}"


def money_claim(field, amount, currency="COP", unit="millions", tier=SourceTier.OFFICIAL,
                domain="supersociedades.gov.co", doc="aaa", period=FY):
    return Claim(
        field=field,
        value={"amount": amount, "currency": currency, "unit": unit,
               "fiscal_period": period},
        display=f"{amount:,.1f} {unit} {currency} ({period})",
        doc_id=doc, tier=tier, publisher_domain=domain,
        page=1, quote="...", as_of=period, currency=currency, unit=unit,
    )


def text_claim(field, value, tier=SourceTier.SECONDARY, domain="news.example.com",
               doc="bbb"):
    return Claim(field=field, value=value, display=value, doc_id=doc,
                 tier=tier, publisher_domain=domain, quote="...")


def get(fields, name):
    return next(f for f in fields if f.field == name)


def test_two_independent_sources_verified():
    claims = [
        text_claim("sector", "Oil & Gas", SourceTier.OFFICIAL, "rues.org.co", "a"),
        text_claim("sector", "oil & gas", SourceTier.SECONDARY, "reuters.com", "b"),
    ]
    field = get(audit(claims), "sector")
    assert field.status == FieldStatus.VERIFIED
    assert field.confidence > 0.9


def test_single_official_source():
    claims = [text_claim("sector", "Oil & Gas", SourceTier.OFFICIAL, "rues.org.co")]
    field = get(audit(claims), "sector")
    assert field.status == FieldStatus.SINGLE_SOURCE


def test_single_secondary_source_unverified():
    claims = [text_claim("sector", "Oil & Gas")]
    field = get(audit(claims), "sector")
    assert field.status == FieldStatus.UNVERIFIED


def test_conflict_is_flagged_and_official_wins():
    claims = [
        text_claim("legal_name", "ECOPETROL S.A.", SourceTier.OFFICIAL,
                   "rues.org.co", "a"),
        text_claim("legal_name", "Ecopetrol Group Holdings", SourceTier.SECONDARY,
                   "blog.example.com", "b"),
    ]
    field = get(audit(claims), "legal_name")
    assert field.status == FieldStatus.FLAGGED
    assert field.display == "ECOPETROL S.A."  # authority weighting
    assert any("conflicting" in n for n in field.notes)


def test_authority_weighting_official_beats_press():
    claims = [
        money_claim("revenue", 100_000, doc="a"),
        money_claim("revenue", 150_000, tier=SourceTier.SECONDARY,
                    domain="news.example.com", doc="b"),
        money_claim("revenue", 150_000, tier=SourceTier.SECONDARY,
                    domain="other.example.com", doc="c"),
    ]
    field = get(audit(claims), "revenue")
    # Two press sources agree with each other, but the regulator filing wins.
    assert "100,000.0" in field.display
    assert field.status == FieldStatus.FLAGGED  # conflict still surfaced


def test_stale_financials_flagged_as_unverified():
    claims = [money_claim("revenue", 100_000, period=OLD_FY)]
    field = get(audit(claims), "revenue")
    assert field.status == FieldStatus.UNVERIFIED
    assert any("fiscal year" in n for n in field.notes)


def test_same_currency_tolerance_corroborates():
    claims = [
        money_claim("revenue", 100_000, doc="a"),
        money_claim("revenue", 101_000, tier=SourceTier.PRIMARY,
                    domain="company.com", doc="b"),  # within 5%
    ]
    field = get(audit(claims), "revenue")
    assert field.status == FieldStatus.VERIFIED


def test_cross_currency_agreement():
    # 4,000,000 million COP ~= 1,000 million USD at the sanity FX rate.
    claims = [
        money_claim("revenue", 4_000_000, currency="COP", doc="a"),
        money_claim("revenue", 1_000, currency="USD", tier=SourceTier.PRIMARY,
                    domain="company.com", doc="b"),
    ]
    field = get(audit(claims), "revenue")
    assert field.status == FieldStatus.VERIFIED


def test_revenue_headcount_unit_error_flagged():
    claims = [
        # 50 *units* of COP for 10,000 employees -> absurd ratio.
        money_claim("revenue", 50, unit="units", doc="a"),
        Claim(field="employees", value=10_000.0, display="10,000",
              doc_id="b", tier=SourceTier.PRIMARY,
              publisher_domain="company.com", quote="..."),
    ]
    fields = audit(claims)
    assert get(fields, "revenue").status == FieldStatus.FLAGGED
    assert any("unit error" in n for n in get(fields, "revenue").notes)


def test_ebitda_above_revenue_flagged():
    claims = [
        money_claim("revenue", 100_000, doc="a"),
        money_claim("ebitda", 500_000, doc="a"),
    ]
    fields = audit(claims)
    assert get(fields, "ebitda").status == FieldStatus.FLAGGED


def test_currency_inconsistency_flagged():
    claims = [
        money_claim("revenue", 100_000, currency="COP", doc="a"),
        money_claim("net_debt", 30, currency="USD", doc="a"),
    ]
    fields = audit(claims)
    assert any("currency inconsistency" in n for n in get(fields, "revenue").notes)


def test_list_fields_cluster_not_conflict():
    claims = [
        text_claim("executives", "Ana Gomez — CEO", SourceTier.PRIMARY,
                   "company.com", "a"),
        text_claim("executives", "Luis Rios — CFO", SourceTier.PRIMARY,
                   "company.com", "a"),
    ]
    fields = [f for f in audit(claims) if f.field == "executives"]
    assert len(fields) == 2
    assert all(f.status != FieldStatus.FLAGGED for f in fields)
