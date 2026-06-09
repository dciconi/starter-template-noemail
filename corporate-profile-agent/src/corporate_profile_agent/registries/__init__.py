from __future__ import annotations

from .base import OfficialSource, RegistryAdapter, RegistryCandidate
from .chile import ChileRegistry
from .colombia import ColombiaRegistry

_REGISTRIES: dict[str, RegistryAdapter] = {
    "CO": ColombiaRegistry(),
    "CL": ChileRegistry(),
}


def get_registry(country: str) -> RegistryAdapter | None:
    return _REGISTRIES.get(country.upper())


__all__ = [
    "ChileRegistry",
    "ColombiaRegistry",
    "OfficialSource",
    "RegistryAdapter",
    "RegistryCandidate",
    "get_registry",
]
