"""Validation loop: diff extracted figures against Supersociedades open data.

Supersociedades republishes filed financial statements (the SIREM lineage)
as structured open data on datos.gov.co — long format, one row per
(nit, concepto, periodo, valor). Because our pipeline extracts the same
figures independently from PDFs/filings, diffing the two gives a field-level
accuracy metric with zero human calls.

Caveats:
* Coverage is Supersociedades-supervised companies. Listed issuers (e.g.
  Ecopetrol) file with Superfinanciera and won't appear here.
* `valor` scale varies by filing (most are thousands of COP). We pick the
  scale in {1, 1e3, 1e6} that minimizes the relative diff and report it, so
  a "match at x1000" is distinguishable from a true unit error.

Usage:
    python eval/diff_against_sirem.py data/            # all generated profiles
    python eval/diff_against_sirem.py data/899999068-1 # one profile
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import httpx

SOCRATA_BASE = "https://www.datos.gov.co/resource"
DATASET = os.environ.get("CPA_SIREM_DATASET", "prwj-nzxa")
TOLERANCE = 0.05  # 5% relative difference counts as a match

REVENUE_CONCEPTO = "Ingresos de actividades ordinarias"
SCALES = (1.0, 1e3, 1e6)

UNIT_MULTIPLIER = {"units": 1.0, "thousands": 1e3, "millions": 1e6, "billions": 1e9}


def fetch_ground_truth_revenue(nit_body: str) -> float | None:
    url = (
        f"{SOCRATA_BASE}/{DATASET}.json"
        f"?nit={nit_body}&concepto={REVENUE_CONCEPTO}"
        "&$order=fecha_corte DESC&$limit=5"
    )
    try:
        resp = httpx.get(url, timeout=30)
        resp.raise_for_status()
        rows = resp.json()
    except Exception:
        return None
    # Prefer the current period of the most recent filing.
    rows.sort(
        key=lambda r: (r.get("fecha_corte", ""), r.get("periodo", "") == "Periodo Actual"),
        reverse=True,
    )
    for row in rows:
        try:
            return float(str(row["valor"]).replace(",", ""))
        except (KeyError, ValueError):
            continue
    return None


def extracted_revenue_cop(profile: dict) -> float | None:
    for field in profile.get("fields", []):
        if field["field"] != "revenue" or not field["supporting_claims"]:
            continue
        claim = field["supporting_claims"][0]
        value = claim.get("value")
        if not isinstance(value, dict):
            continue
        if (claim.get("currency") or "").upper() != "COP":
            return None  # only compare like-for-like
        return value["amount"] * UNIT_MULTIPLIER.get(claim.get("unit") or "units", 1.0)
    return None


def best_scale_diff(ours: float, truth_raw: float) -> tuple[float, float]:
    """Return (relative diff, scale) minimizing |ours - truth*scale|/|ours|."""
    best = (float("inf"), 1.0)
    for scale in SCALES:
        truth = truth_raw * scale
        hi = max(abs(ours), abs(truth))
        if hi == 0:
            continue
        rel = abs(ours - truth) / hi
        if rel < best[0]:
            best = (rel, scale)
    return best


def evaluate(profile_path: Path) -> tuple[str, bool | None, str]:
    profile = json.loads(profile_path.read_text())
    nit = profile["entity"].get("tax_id", "")
    if not nit:
        return profile_path.parent.name, None, "no resolved NIT"
    nit_body = nit.split("-")[0]

    truth_raw = fetch_ground_truth_revenue(nit_body)
    if truth_raw is None:
        return nit, None, "no Supersociedades revenue row (listed issuer?)"

    ours = extracted_revenue_cop(profile)
    if ours is None:
        return nit, None, "no comparable extracted revenue in COP"

    rel, scale = best_scale_diff(ours, truth_raw)
    ok = rel <= TOLERANCE
    return nit, ok, (
        f"ours={ours:,.0f} COP, sirem={truth_raw:,.0f} (x{scale:g}), diff={rel:.1%}"
    )


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "data")
    profiles = sorted(root.glob("**/profile.json"))
    if not profiles:
        print(f"no profile.json under {root}", file=sys.stderr)
        return 1

    matched = comparable = 0
    for path in profiles:
        nit, ok, detail = evaluate(path)
        marker = "?" if ok is None else "OK" if ok else "MISMATCH"
        print(f"[{marker:>8}] {nit}: {detail}")
        if ok is not None:
            comparable += 1
            matched += int(ok)

    if comparable:
        print(f"\nrevenue field accuracy: {matched}/{comparable} "
              f"({matched / comparable:.0%}) within {TOLERANCE:.0%}")
    else:
        print("\nno comparable profiles")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
