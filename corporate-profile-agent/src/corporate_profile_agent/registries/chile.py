"""Chile — second registry adapter (listed companies via CMF).

The CMF (Comisión para el Mercado Financiero) publishes supervised-entity
records and standardized financial statements (FECU/IFRS) for issuers.
Name search has no stable public API, so resolution requires an explicit RUT;
official_sources then points at the CMF entity page and filings index.
"""

from __future__ import annotations

from .base import OfficialSource, RegistryAdapter, RegistryCandidate

CMF_ENTITY_URL = (
    "https://www.cmfchile.cl/institucional/mercados/entidad.php"
    "?mercado=V&rut={rut}&tipoentidad=RVEMI"
)


class ChileRegistry(RegistryAdapter):
    name = "CMF"
    country = "CL"

    def search_by_name(self, normalized_name: str) -> list[RegistryCandidate]:
        # No public name-search endpoint; require an explicit RUT.
        return []

    def official_sources(self, tax_id: str) -> list[OfficialSource]:
        rut_body = tax_id.split("-")[0]
        return [
            OfficialSource(
                url=CMF_ENTITY_URL.format(rut=rut_body),
                title="CMF supervised-entity record",
                kind="registry_record",
            ),
        ]
