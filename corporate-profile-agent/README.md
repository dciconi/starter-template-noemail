# corporate-profile-agent

Generates **audited corporate profiles** for Latin American companies as a
six-stage pipeline. The thesis: generic AI research tools do badly here
because they ignore local registries and PDF-buried financials — the leverage
is LatAm registry plumbing plus a deterministic audit layer.

## Pipeline

| Stage | Module | What it does |
|---|---|---|
| 1. Intake & entity resolution | `stages/intake.py`, `tax_ids.py` | Normalizes input and anchors it to the official ID (CNPJ, RFC, NIT, RUT, CUIT, RUC) with real checksum validation. Everything downstream keys off the ID, never the name. Homonyms surface as explicit ambiguity instead of a silent pick. |
| 2. Source discovery | `stages/discovery.py`, `registries/` | Tier 1 (registries/regulators) comes deterministically from country adapters. Tiers 2–3 (IR PDFs, press, news, hiring signals) via Claude + server-side web search, returned as structured candidates. |
| 3. Document acquisition | `stages/acquisition.py` | Downloads every source, stores it with URL + retrieval date + SHA-256, parses PDFs with table extraction, and OCRs scanned pages (Spanish + Portuguese) when needed. |
| 4. Extraction | `stages/extraction.py`, `models.py` | One structured-output Claude call **per document** into a fixed schema. Every value carries a citation (page + verbatim quote). Native PDFs are sent as document blocks so page cites line up with the file. |
| 5. Audit (the moat) | `stages/audit.py` | Deterministic, LLM-free: cross-validation (≥2 independent domains), authority weighting (regulator > company > news), recency flags, sanity checks (revenue/headcount ratio, currency consistency, EBITDA ≤ revenue, thousands-vs-millions errors), per-field confidence scores. |
| 6. Synthesis | `stages/synthesis.py` | Markdown report rendered **only from the validated schema**. Flagged/unverified data is excluded from the narrative and listed explicitly, with a sources table and per-field confidence notes. |

## v1 scope

Colombia first (RUES name resolution + Supersociedades/SIREM open data),
Chile second (CMF). Other countries accept an explicit tax ID and tier-2/3
discovery only.

## Setup

```bash
cd corporate-profile-agent
pip install -e ".[pdf,dev]"           # pdf extras need system tesseract-ocr
export ANTHROPIC_API_KEY=sk-ant-...
```

Without an API key the deterministic stages (intake, audit, synthesis) and
the test suite still run; discovery/extraction are skipped with a warning.

## Usage

```bash
python -m corporate_profile_agent \
  --name "Ecopetrol" --country CO --tax-id 899999068-1
```

Outputs land in `data/<tax_id>/`:

- `docs/` — every retrieved document plus `manifest.json` (URL, date, hash)
- `profile.json` — the audited schema with claims, citations, confidence
- `profile.md` — the report

## Validation loop (zero human calls)

Supersociedades publishes filed financials as open data. Generate profiles
for N Colombian companies, then diff the extracted figures against the
regulator's structured dataset:

```bash
python eval/diff_against_sirem.py data/
```

Prints per-company match/mismatch and aggregate field-level accuracy.

## Tests

```bash
pytest
```

Covers tax-ID checksums for all six jurisdictions, the audit rules
(corroboration, conflicts, recency, sanity checks, confidence scoring), and
the synthesis guarantee that unaudited data never leaks into the narrative.

## Configuration

| Env var | Default | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | Required for discovery + extraction |
| `CPA_MODEL` | `claude-opus-4-8` | Extraction/discovery model |
| `CPA_DATA_DIR` | `./data` | Output root |
| `CPA_SIREM_DATASET` | `prwj-nzxa` | datos.gov.co Socrata resource id (income statement) |
