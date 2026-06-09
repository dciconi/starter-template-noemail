"""Registry adapter interface.

One adapter per country wraps that jurisdiction's official registry and
regulator endpoints. Adapters do two jobs:

* ``search_by_name`` — entity resolution (stage 1)
* ``official_sources`` — tier-1 source discovery for a resolved ID (stage 2)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class RegistryCandidate:
    name: str
    tax_id: str
    status: str = ""          # e.g. ACTIVA, CANCELADA
    municipality: str = ""


@dataclass
class OfficialSource:
    url: str
    title: str
    kind: str = "filing"      # filing | registry_record | dataset
    params: dict = field(default_factory=dict)


class RegistryAdapter(ABC):
    name: str = "base"
    country: str = ""

    @abstractmethod
    def search_by_name(self, normalized_name: str) -> list[RegistryCandidate]:
        """Return registry candidates for a normalized company name."""

    @abstractmethod
    def official_sources(self, tax_id: str) -> list[OfficialSource]:
        """Return tier-1 URLs (registry records, regulator filings, open
        datasets) for a resolved tax ID."""
