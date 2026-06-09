"""Official tax/registry ID validation for LatAm jurisdictions.

Every entity in the pipeline is anchored to one of these IDs — never to a
name. Each validator normalizes formatting (dots, dashes, slashes) and runs
the official checksum algorithm where one exists.

Supported:
    BR  CNPJ  (14 digits, two mod-11 check digits)
    CL  RUT   (7-8 digits + mod-11 check digit, 'K' allowed)
    CO  NIT   (digits + prime-weighted mod-11 check digit)
    AR  CUIT  (11 digits, mod-11 check digit)
    PE  RUC   (11 digits, mod-11 check digit)
    MX  RFC   (12/13 chars, structural validation: no public checksum needed
               for entity resolution since SAT validates server-side)
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class TaxIdResult:
    valid: bool
    normalized: str
    country: str
    id_type: str
    reason: str = ""


def _digits(raw: str) -> str:
    return re.sub(r"\D", "", raw)


# --- Brazil: CNPJ ----------------------------------------------------------

def validate_cnpj(raw: str) -> TaxIdResult:
    cnpj = _digits(raw)
    if len(cnpj) != 14:
        return TaxIdResult(False, cnpj, "BR", "CNPJ", "must be 14 digits")
    if cnpj == cnpj[0] * 14:
        return TaxIdResult(False, cnpj, "BR", "CNPJ", "repeated digits")

    def check_digit(digits: str, weights: list[int]) -> int:
        total = sum(int(d) * w for d, w in zip(digits, weights))
        dv = 11 - (total % 11)
        return 0 if dv >= 10 else dv

    dv1 = check_digit(cnpj[:12], [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    dv2 = check_digit(cnpj[:13], [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    if (int(cnpj[12]), int(cnpj[13])) != (dv1, dv2):
        return TaxIdResult(False, cnpj, "BR", "CNPJ", "checksum mismatch")
    return TaxIdResult(True, cnpj, "BR", "CNPJ")


# --- Chile: RUT ------------------------------------------------------------

def validate_rut(raw: str) -> TaxIdResult:
    cleaned = re.sub(r"[.\s-]", "", raw).upper()
    if not re.fullmatch(r"\d{7,8}[\dK]", cleaned):
        return TaxIdResult(False, cleaned, "CL", "RUT", "bad format")
    body, dv = cleaned[:-1], cleaned[-1]
    total, factor = 0, 2
    for digit in reversed(body):
        total += int(digit) * factor
        factor = 2 if factor == 7 else factor + 1
    rem = 11 - (total % 11)
    expected = "0" if rem == 11 else "K" if rem == 10 else str(rem)
    if dv != expected:
        return TaxIdResult(False, cleaned, "CL", "RUT", "checksum mismatch")
    return TaxIdResult(True, f"{body}-{dv}", "CL", "RUT")


# --- Colombia: NIT ---------------------------------------------------------

_NIT_PRIMES = [3, 7, 13, 17, 19, 23, 29, 37, 41, 43, 47, 53, 59, 67, 71]


def nit_check_digit(body: str) -> int:
    """Compute the DIAN check digit for a NIT body (digits only, no DV)."""
    body = _digits(body)
    total = sum(int(d) * p for d, p in zip(reversed(body), _NIT_PRIMES))
    rem = total % 11
    return rem if rem <= 1 else 11 - rem


def validate_nit(raw: str) -> TaxIdResult:
    cleaned = _digits(raw)
    if len(cleaned) < 4 or len(cleaned) > 16:
        return TaxIdResult(False, cleaned, "CO", "NIT", "bad length")
    body, dv = cleaned[:-1], int(cleaned[-1])
    total = sum(
        int(d) * p for d, p in zip(reversed(body), _NIT_PRIMES)
    )
    rem = total % 11
    expected = rem if rem <= 1 else 11 - rem
    if dv != expected:
        return TaxIdResult(False, cleaned, "CO", "NIT", "checksum mismatch")
    return TaxIdResult(True, f"{body}-{dv}", "CO", "NIT")


# --- Argentina: CUIT -------------------------------------------------------

def validate_cuit(raw: str) -> TaxIdResult:
    cuit = _digits(raw)
    if len(cuit) != 11:
        return TaxIdResult(False, cuit, "AR", "CUIT", "must be 11 digits")
    weights = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
    total = sum(int(d) * w for d, w in zip(cuit[:10], weights))
    rem = 11 - (total % 11)
    expected = 0 if rem == 11 else 9 if rem == 10 else rem
    if int(cuit[10]) != expected:
        return TaxIdResult(False, cuit, "AR", "CUIT", "checksum mismatch")
    return TaxIdResult(True, f"{cuit[:2]}-{cuit[2:10]}-{cuit[10]}", "AR", "CUIT")


# --- Peru: RUC -------------------------------------------------------------

def validate_ruc(raw: str) -> TaxIdResult:
    ruc = _digits(raw)
    if len(ruc) != 11:
        return TaxIdResult(False, ruc, "PE", "RUC", "must be 11 digits")
    if ruc[:2] not in {"10", "15", "16", "17", "20"}:
        return TaxIdResult(False, ruc, "PE", "RUC", "invalid type prefix")
    weights = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
    total = sum(int(d) * w for d, w in zip(ruc[:10], weights))
    expected = (11 - (total % 11)) % 10
    if int(ruc[10]) != expected:
        return TaxIdResult(False, ruc, "PE", "RUC", "checksum mismatch")
    return TaxIdResult(True, ruc, "PE", "RUC")


# --- Mexico: RFC -----------------------------------------------------------

_RFC_PATTERN = re.compile(
    r"^([A-ZÑ&]{3,4})(\d{2})(\d{2})(\d{2})([A-Z\d]{3})$"
)


def validate_rfc(raw: str) -> TaxIdResult:
    rfc = re.sub(r"[\s-]", "", raw).upper()
    match = _RFC_PATTERN.fullmatch(rfc)
    if not match:
        return TaxIdResult(False, rfc, "MX", "RFC", "bad format")
    _, _, month, day, _ = match.groups()
    if not (1 <= int(month) <= 12 and 1 <= int(day) <= 31):
        return TaxIdResult(False, rfc, "MX", "RFC", "invalid embedded date")
    # 12 chars = persona moral (company), 13 = persona física (individual)
    kind = "company" if len(rfc) == 12 else "individual"
    return TaxIdResult(True, rfc, "MX", "RFC", kind)


VALIDATORS = {
    "BR": validate_cnpj,
    "CL": validate_rut,
    "CO": validate_nit,
    "AR": validate_cuit,
    "PE": validate_ruc,
    "MX": validate_rfc,
}


def validate(country: str, raw: str) -> TaxIdResult:
    """Validate a tax ID for the given ISO 3166-1 alpha-2 country code."""
    country = country.upper()
    if country not in VALIDATORS:
        return TaxIdResult(False, raw, country, "?", f"unsupported country {country}")
    return VALIDATORS[country](raw)
