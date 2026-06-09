"""Colombia — the v1 country.

Tier-1 plumbing:

* RUES (Registro Único Empresarial y Social) — national business registry,
  public search API. Resolves names -> NIT and gives legal status.
* SIREM / Superintendencia de Sociedades — supervised companies file full
  financial statements, republished as open data on datos.gov.co (Socrata).
  This is also the ground-truth dataset the eval script diffs against.
* SIMEV/RNVE (Superfinanciera) — issuers' filings, for listed companies.

Network calls are isolated here so the rest of the pipeline stays testable
offline.
"""

from __future__ import annotations

import logging

import httpx

from .base import OfficialSource, RegistryAdapter, RegistryCandidate

log = logging.getLogger(__name__)

RUES_SEARCH_URL = "https://www.rues.org.co/api/consultasRUES/ConsultaNIT_RM"
# Socrata datasets: Supersociedades "Estados Financieros NIIF" (SIREM
# successor) on datos.gov.co. Long format: one row per
# (nit, concepto, periodo, valor). prwj-nzxa = income statement,
# pfdp-zks5 = balance sheet. Override via CPA_SIREM_DATASET if it rotates.
SOCRATA_BASE = "https://www.datos.gov.co/resource"
DEFAULT_SIREM_DATASET = "prwj-nzxa"


class ColombiaRegistry(RegistryAdapter):
    name = "RUES"
    country = "CO"

    def __init__(self, sirem_dataset: str = DEFAULT_SIREM_DATASET, timeout: float = 30.0):
        self.sirem_dataset = sirem_dataset
        self.timeout = timeout

    def search_by_name(self, normalized_name: str) -> list[RegistryCandidate]:
        try:
            resp = httpx.post(
                RUES_SEARCH_URL,
                json={"razonSocial": normalized_name},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            payload = resp.json()
        except Exception as exc:  # network/schema drift must not kill intake
            log.warning("RUES search failed: %s", exc)
            return []

        candidates = []
        for row in payload.get("registros", payload if isinstance(payload, list) else []):
            nit = str(row.get("nit", "")).strip()
            dv = str(row.get("dv", "")).strip()
            if not nit:
                continue
            candidates.append(
                RegistryCandidate(
                    name=row.get("razon_social", row.get("razonSocial", "")),
                    tax_id=f"{nit}-{dv}" if dv else nit,
                    status=row.get("estado_matricula", row.get("estado", "")),
                    municipality=row.get("municipio", ""),
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
