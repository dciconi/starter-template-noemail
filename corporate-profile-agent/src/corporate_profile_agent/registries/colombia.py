"""Colombia — the v1 country.

Tier-1 plumbing:

* Name resolution via the Supersociedades "10,000 largest companies" open
  dataset (datos.gov.co, Socrata). The RUES public API sits behind a SPA /
  WAF and returns no usable JSON, so we resolve names against open data
  instead and compute the NIT check digit locally. Coverage is the ~10k
  largest filers — good enough for the listed/large-cap v1 scope.
* SIREM / Superintendencia de Sociedades — supervised companies file full
  financial statements, republished as open data. This is also the
  ground-truth dataset the eval script diffs against.
* SIMEV/RNVE (Superfinanciera) — issuers' filings, for listed companies.

Network calls are isolated here so the rest of the pipeline stays testable
offline.
"""

from __future__ import annotations

import logging
import unicodedata

import httpx

from .. import tax_ids
from .base import OfficialSource, RegistryAdapter, RegistryCandidate

log = logging.getLogger(__name__)

SOCRATA_BASE = "https://www.datos.gov.co/resource"
# Directory dataset: NIT, razon_social, supervisor, sector for the largest
# Colombian companies. Public, queryable, no auth.
DIRECTORY_DATASET = "6cat-2gcs"
# Supersociedades "Estados Financieros NIIF" (SIREM successor). Long format:
# one row per (nit, concepto, periodo, valor). prwj-nzxa = income statement,
# pfdp-zks5 = balance sheet. Override via CPA_SIREM_DATASET if it rotates.
DEFAULT_SIREM_DATASET = "prwj-nzxa"


def _strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c))


class ColombiaRegistry(RegistryAdapter):
    name = "Supersociedades open data"
    country = "CO"

    def __init__(self, sirem_dataset: str = DEFAULT_SIREM_DATASET, timeout: float = 30.0):
        self.sirem_dataset = sirem_dataset
        self.timeout = timeout

    def search_by_name(self, normalized_name: str) -> list[RegistryCandidate]:
        # Socrata full-text search ($q) over the directory dataset, then
        # de-dup by NIT and attach a locally-computed check digit.
        try:
            resp = httpx.get(
                f"{SOCRATA_BASE}/{DIRECTORY_DATASET}.json",
                params={
                    "$select": "nit,raz_n_social,supervisor,ciudad_domicilio",
                    "$q": _strip_accents(normalized_name),
                    "$limit": 25,
                },
                timeout=self.timeout,
            )
            resp.raise_for_status()
            rows = resp.json()
        except Exception as exc:  # network/schema drift must not kill intake
            log.warning("directory search failed: %s", exc)
            return []

        target = _strip_accents(normalized_name).lower()
        seen: set[str] = set()
        candidates: list[RegistryCandidate] = []
        for row in rows:
            nit_body = str(row.get("nit", "")).strip()
            if not nit_body or nit_body in seen:
                continue
            seen.add(nit_body)
            name = row.get("raz_n_social", "")
            # Keep only rows whose name actually contains the query tokens —
            # $q is fuzzy and will return loosely-related companies.
            if target not in _strip_accents(name).lower():
                continue
            dv = tax_ids.nit_check_digit(nit_body)
            candidates.append(
                RegistryCandidate(
                    name=name,
                    tax_id=f"{nit_body}-{dv}",
                    status=row.get("supervisor", ""),
                    municipality=row.get("ciudad_domicilio", ""),
                )
            )
        return candidates

    def official_sources(self, tax_id: str) -> list[OfficialSource]:
        nit_body = tax_id.split("-")[0]
        return [
            OfficialSource(
                url=f"https://www.rues.org.co/?nit={nit_body}",
                title="RUES registry record",
                kind="registry_record",
            ),
            OfficialSource(
                url=(
                    f"{SOCRATA_BASE}/{self.sirem_dataset}.json"
                    f"?nit={nit_body}"
                    "&$order=fecha_corte DESC&$limit=200"
                ),
                title="Supersociedades income statement (open data)",
                kind="dataset",
            ),
        ]
